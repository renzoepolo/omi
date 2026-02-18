import csv
import datetime as dt
import sqlite3
from pathlib import Path

import pytest

from exporter import ProjectExporter, ProjectRecord, TenantSecurityError


@pytest.fixture
def sample_records() -> list[ProjectRecord]:
    return [
        ProjectRecord(
            id=1,
            tenant_id="tenant-a",
            status_code="active",
            created_at=dt.date(2025, 1, 10),
            project_type_code="INFRA",
            name="Proyecto A",
            latitude=19.4326,
            longitude=-99.1332,
        ),
        ProjectRecord(
            id=2,
            tenant_id="tenant-a",
            status_code="closed",
            created_at=dt.date(2025, 1, 15),
            project_type_code="SOC",
            name="Proyecto B",
            latitude=20.0,
            longitude=-100.0,
        ),
        ProjectRecord(
            id=3,
            tenant_id="tenant-b",
            status_code="active",
            created_at=dt.date(2025, 1, 20),
            project_type_code="ENV",
            name="Proyecto C",
            latitude=21.0,
            longitude=-101.0,
        ),
    ]


def test_csv_plano_aplica_filtros_y_tenant(tmp_path: Path, sample_records: list[ProjectRecord]):
    exporter = ProjectExporter(sample_records)
    output = exporter.export_csv_plano(
        tmp_path / "plano.csv",
        tenant_id="tenant-a",
        statuses=["active"],
        start_date=dt.date(2025, 1, 1),
        end_date=dt.date(2025, 1, 12),
    )

    with output.open(encoding="utf-8") as fp:
        rows = list(csv.reader(fp))

    assert len(rows) == 2  # encabezado + 1 dato
    assert rows[1][0] == "1"
    assert rows[1][2] == "active"


def test_csv_interpretado_convierte_catalogos(tmp_path: Path, sample_records: list[ProjectRecord]):
    exporter = ProjectExporter(sample_records)
    output = exporter.export_csv_interpretado(
        tmp_path / "interpretado.csv",
        tenant_id="tenant-a",
        statuses=["closed"],
    )

    with output.open(encoding="utf-8") as fp:
        rows = list(csv.reader(fp))

    assert rows[1][2] == "Cerrado"
    assert rows[1][4] == "Social"


def test_tenant_obligatorio(sample_records: list[ProjectRecord], tmp_path: Path):
    exporter = ProjectExporter(sample_records)
    with pytest.raises(TenantSecurityError):
        exporter.export_csv_plano(tmp_path / "x.csv", tenant_id="")


def test_geopackage_incluye_atributos_y_geom(tmp_path: Path, sample_records: list[ProjectRecord]):
    exporter = ProjectExporter(sample_records)
    gpkg = exporter.export_geopackage(
        tmp_path / "projects.gpkg",
        tenant_id="tenant-a",
        statuses=["active", "closed"],
        end_date=dt.date(2025, 1, 15),
    )

    con = sqlite3.connect(gpkg)
    try:
        cur = con.cursor()
        count = cur.execute("SELECT COUNT(*) FROM project_exports").fetchone()[0]
        assert count == 2
        geom = cur.execute("SELECT geom FROM project_exports LIMIT 1").fetchone()[0]
        assert isinstance(geom, bytes)
        assert geom[:2] == b"GP"
    finally:
        con.close()
