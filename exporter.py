from __future__ import annotations

import csv
import datetime as dt
import sqlite3
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ProjectRecord:
    """Record source for project exports."""

    id: int
    tenant_id: str
    status_code: str
    created_at: dt.date
    project_type_code: str
    name: str
    latitude: float
    longitude: float


STATUS_LABELS = {
    "draft": "Borrador",
    "active": "Activo",
    "paused": "Pausado",
    "closed": "Cerrado",
}

PROJECT_TYPE_LABELS = {
    "INFRA": "Infraestructura",
    "SOC": "Social",
    "ENV": "Ambiental",
}


class TenantSecurityError(ValueError):
    """Raised when tenant constraints are missing or invalid."""


class ProjectExporter:
    """Exports project datasets with mandatory tenant isolation."""

    def __init__(self, records: Iterable[ProjectRecord]):
        self._records = list(records)

    def _filter(
        self,
        *,
        tenant_id: str,
        statuses: Sequence[str] | None = None,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
    ) -> list[ProjectRecord]:
        if not tenant_id:
            raise TenantSecurityError("tenant_id es obligatorio para exportar")

        status_set = set(statuses or [])

        result: list[ProjectRecord] = []
        for item in self._records:
            if item.tenant_id != tenant_id:
                continue
            if status_set and item.status_code not in status_set:
                continue
            if start_date and item.created_at < start_date:
                continue
            if end_date and item.created_at > end_date:
                continue
            result.append(item)
        return result

    def export_csv_plano(
        self,
        output_path: str | Path,
        *,
        tenant_id: str,
        statuses: Sequence[str] | None = None,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
    ) -> Path:
        rows = self._filter(
            tenant_id=tenant_id,
            statuses=statuses,
            start_date=start_date,
            end_date=end_date,
        )
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(
                [
                    "id",
                    "tenant_id",
                    "status_code",
                    "created_at",
                    "project_type_code",
                    "name",
                    "latitude",
                    "longitude",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row.id,
                        row.tenant_id,
                        row.status_code,
                        row.created_at.isoformat(),
                        row.project_type_code,
                        row.name,
                        row.latitude,
                        row.longitude,
                    ]
                )

        return output

    def export_csv_interpretado(
        self,
        output_path: str | Path,
        *,
        tenant_id: str,
        statuses: Sequence[str] | None = None,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
    ) -> Path:
        rows = self._filter(
            tenant_id=tenant_id,
            statuses=statuses,
            start_date=start_date,
            end_date=end_date,
        )
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(
                [
                    "id",
                    "tenant_id",
                    "estado",
                    "fecha_creacion",
                    "tipo_proyecto",
                    "nombre",
                    "latitude",
                    "longitude",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row.id,
                        row.tenant_id,
                        STATUS_LABELS.get(row.status_code, row.status_code),
                        row.created_at.isoformat(),
                        PROJECT_TYPE_LABELS.get(
                            row.project_type_code,
                            row.project_type_code,
                        ),
                        row.name,
                        row.latitude,
                        row.longitude,
                    ]
                )

        return output

    def export_geopackage(
        self,
        output_path: str | Path,
        *,
        tenant_id: str,
        statuses: Sequence[str] | None = None,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
        table_name: str = "project_exports",
    ) -> Path:
        rows = self._filter(
            tenant_id=tenant_id,
            statuses=statuses,
            start_date=start_date,
            end_date=end_date,
        )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            output.unlink()

        con = sqlite3.connect(output)
        try:
            cur = con.cursor()
            cur.executescript(
                """
                PRAGMA application_id = 1196437808;
                PRAGMA user_version = 10300;

                CREATE TABLE gpkg_spatial_ref_sys (
                    srs_name TEXT NOT NULL,
                    srs_id INTEGER NOT NULL PRIMARY KEY,
                    organization TEXT NOT NULL,
                    organization_coordsys_id INTEGER NOT NULL,
                    definition TEXT NOT NULL,
                    description TEXT
                );

                CREATE TABLE gpkg_contents (
                    table_name TEXT NOT NULL PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    identifier TEXT UNIQUE,
                    description TEXT DEFAULT '',
                    last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    min_x DOUBLE,
                    min_y DOUBLE,
                    max_x DOUBLE,
                    max_y DOUBLE,
                    srs_id INTEGER,
                    FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
                );

                CREATE TABLE gpkg_geometry_columns (
                    table_name TEXT NOT NULL,
                    column_name TEXT NOT NULL,
                    geometry_type_name TEXT NOT NULL,
                    srs_id INTEGER NOT NULL,
                    z TINYINT NOT NULL,
                    m TINYINT NOT NULL,
                    PRIMARY KEY (table_name, column_name),
                    FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name),
                    FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
                );
                """
            )
            cur.execute(
                """
                INSERT INTO gpkg_spatial_ref_sys
                (srs_name, srs_id, organization, organization_coordsys_id, definition, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "WGS 84 geodetic",
                    4326,
                    "EPSG",
                    4326,
                    "GEOGCS[\"WGS 84\",DATUM[\"World Geodetic System 1984\",SPHEROID[\"WGS 84\",6378137,298.257223563]],PRIMEM[\"Greenwich\",0],UNIT[\"degree\",0.0174532925199433]]",
                    "",
                ),
            )

            cur.execute(
                f"""
                CREATE TABLE {table_name} (
                    fid INTEGER PRIMARY KEY AUTOINCREMENT,
                    geom BLOB NOT NULL,
                    id INTEGER NOT NULL,
                    tenant_id TEXT NOT NULL,
                    status_code TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    project_type_code TEXT NOT NULL,
                    name TEXT NOT NULL
                )
                """
            )

            cur.execute(
                """
                INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id)
                VALUES (?, 'features', ?, 4326)
                """,
                (table_name, table_name),
            )
            cur.execute(
                """
                INSERT INTO gpkg_geometry_columns (table_name, column_name, geometry_type_name, srs_id, z, m)
                VALUES (?, 'geom', 'POINT', 4326, 0, 0)
                """,
                (table_name,),
            )

            for row in rows:
                geom = _gpkg_point_blob(row.longitude, row.latitude)
                cur.execute(
                    f"""
                    INSERT INTO {table_name}
                    (geom, id, tenant_id, status_code, created_at, project_type_code, name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        geom,
                        row.id,
                        row.tenant_id,
                        row.status_code,
                        row.created_at.isoformat(),
                        row.project_type_code,
                        row.name,
                    ),
                )

            con.commit()
        finally:
            con.close()

        return output


def _gpkg_point_blob(x: float, y: float, srs_id: int = 4326) -> bytes:
    # GeoPackage Binary Header (little endian, empty envelope)
    header = b"GP" + bytes([0, 1]) + struct.pack("<I", srs_id)
    wkb = (
        struct.pack("<B", 1)
        + struct.pack("<I", 1)  # Point type
        + struct.pack("<d", x)
        + struct.pack("<d", y)
    )
    return header + wkb
