from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_project_membership
from app.core.database import get_db
from app.models import Layer, Project, ProjectLayer, User, UserProject

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    memberships = db.scalars(
        select(UserProject)
        .where(UserProject.user_id == current_user.id)
        .order_by(UserProject.project_id.asc())
    ).all()
    project_ids = [m.project_id for m in memberships]
    if not project_ids:
        return []
    projects = db.scalars(select(Project).where(Project.id.in_(project_ids))).all()
    projects_map = {p.id: p for p in projects}
    return [
        _serialize_project_summary(db, projects_map[m.project_id], m.role.value)
        for m in memberships
        if m.project_id in projects_map
    ]


@router.get("/current")
def current_project_context(
    membership: UserProject = Depends(get_project_membership),
) -> dict:
    return {
        "project_id": membership.project_id,
        "role": membership.role.value,
        "user_id": membership.user_id,
    }


def _serialize_project_summary(db: Session, project: Project, role: str) -> dict:
    project_layers = db.scalars(
        select(ProjectLayer).where(ProjectLayer.project_id == project.id).order_by(ProjectLayer.id.asc())
    ).all()
    layer_ids = [row.layer_id for row in project_layers]
    layers_by_id = {}
    if layer_ids:
        layers = db.scalars(select(Layer).where(Layer.id.in_(layer_ids))).all()
        layers_by_id = {layer.id: layer for layer in layers}

    return {
        "id": project.id,
        "name": project.name,
        "role": role,
        "center": [
            project.default_center_lng or -77.0428,
            project.default_center_lat or -12.0464,
        ],
        "zoom": project.default_zoom,
        "default_base_layers": [
            {
                "layer_id": row.layer_id,
                "name": layers_by_id[row.layer_id].name,
                "geoserver_workspace": layers_by_id[row.layer_id].geoserver_workspace,
                "geoserver_layer_name": layers_by_id[row.layer_id].geoserver_layer_name,
                "type": layers_by_id[row.layer_id].type.value,
                "style_name": layers_by_id[row.layer_id].style_name,
                "available_override": (
                    row.available_override
                    if row.available_override is not None
                    else True
                ),
                "default_visible": (
                    row.visible_override
                    if row.visible_override is not None
                    else layers_by_id[row.layer_id].default_visible
                ),
                "z_index": (
                    row.z_index_override
                    if row.z_index_override is not None
                    else layers_by_id[row.layer_id].z_index
                ),
            }
            for row in project_layers
            if row.layer_id in layers_by_id
        ],
    }
