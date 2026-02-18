from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from .db import get_cursor
from .geoserver import (
    GEOSERVER_WORKSPACE,
    bootstrap_geoserver,
    publish_featuretype,
)


app = FastAPI(title="OMI Backend", version="1.0.0")


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class BaseLayerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    service_url: HttpUrl
    layer_type: str = Field(description="Ej: xyz, wmts, wms")


class PropertyCreate(BaseModel):
    project_id: int
    code: str
    owner_name: str | None = None
    lon: float
    lat: float


def ensure_project_properties_view(project_id: int) -> str:
    view_name = f"properties_project_{project_id}"
    with get_cursor() as (conn, cur):
        cur.execute(
            f"""
            CREATE OR REPLACE VIEW {view_name} AS
            SELECT
                id,
                project_id,
                code,
                owner_name,
                geom,
                created_at
            FROM properties
            WHERE project_id = %s
            """,
            (project_id,),
        )
        conn.commit()
    return view_name


def publish_properties_layer_for_project(project_id: int):
    view_name = ensure_project_properties_view(project_id)
    publish_featuretype(view_name)


@app.on_event("startup")
def startup_event():
    bootstrap_geoserver()
    with get_cursor() as (_, cur):
        cur.execute("SELECT id FROM projects ORDER BY id")
        project_ids = [row[0] for row in cur.fetchall()]

    for project_id in project_ids:
        publish_properties_layer_for_project(project_id)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "workspace": GEOSERVER_WORKSPACE,
        "wfst_enabled": False,
    }


@app.post("/projects")
def create_project(payload: ProjectCreate):
    with get_cursor(dict_cursor=True) as (conn, cur):
        try:
            cur.execute(
                "INSERT INTO projects(name) VALUES (%s) RETURNING id, name, created_at",
                (payload.name,),
            )
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=400, detail=f"No se pudo crear proyecto: {exc}")
        project = cur.fetchone()
        conn.commit()

    publish_properties_layer_for_project(project["id"])
    project["properties_layer"] = f"properties_project_{project['id']}"
    return project


@app.get("/projects")
def list_projects():
    with get_cursor(dict_cursor=True) as (_, cur):
        cur.execute(
            """
            SELECT
                id,
                name,
                created_at,
                'properties_project_' || id::text AS properties_layer
            FROM projects
            ORDER BY id
            """
        )
        return cur.fetchall()


@app.post("/projects/{project_id}/base-layers")
def register_base_layer(project_id: int, payload: BaseLayerCreate):
    with get_cursor(dict_cursor=True) as (conn, cur):
        cur.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Proyecto no existe")

        cur.execute(
            """
            INSERT INTO base_layers(name, service_url, layer_type)
            VALUES (%s, %s, %s)
            ON CONFLICT(name, service_url, layer_type)
            DO UPDATE SET name = EXCLUDED.name
            RETURNING id, name, service_url, layer_type, created_at
            """,
            (payload.name, str(payload.service_url), payload.layer_type),
        )
        base_layer = cur.fetchone()

        cur.execute(
            """
            INSERT INTO project_base_layers(project_id, base_layer_id)
            VALUES (%s, %s)
            ON CONFLICT(project_id, base_layer_id) DO NOTHING
            """,
            (project_id, base_layer["id"]),
        )
        conn.commit()

    return {
        "project_id": project_id,
        "base_layer": base_layer,
        "associated": True,
    }


@app.get("/projects/{project_id}/base-layers")
def list_project_base_layers(project_id: int):
    with get_cursor(dict_cursor=True) as (_, cur):
        cur.execute(
            """
            SELECT
                bl.id,
                bl.name,
                bl.service_url,
                bl.layer_type,
                bl.created_at
            FROM project_base_layers pbl
            JOIN base_layers bl ON bl.id = pbl.base_layer_id
            WHERE pbl.project_id = %s
            ORDER BY bl.id
            """,
            (project_id,),
        )
        layers: List[dict] = cur.fetchall()
        return {"project_id": project_id, "base_layers": layers}


@app.post("/properties")
def create_property(payload: PropertyCreate):
    with get_cursor(dict_cursor=True) as (conn, cur):
        cur.execute("SELECT id FROM projects WHERE id = %s", (payload.project_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Proyecto no existe")

        cur.execute(
            """
            INSERT INTO properties(project_id, code, owner_name, geom)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            RETURNING id, project_id, code, owner_name, created_at
            """,
            (
                payload.project_id,
                payload.code,
                payload.owner_name,
                payload.lon,
                payload.lat,
            ),
        )
        record = cur.fetchone()
        conn.commit()

    return record
