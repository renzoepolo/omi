import sqlite3
from pathlib import Path

import bulk_csv_app as app


def setup_function() -> None:
    if Path(app.DB_PATH).exists():
        Path(app.DB_PATH).unlink()
    app.init_db()


def count_rows() -> int:
    with sqlite3.connect(app.DB_PATH) as conn:
        return conn.execute("SELECT COUNT(*) FROM ubicaciones").fetchone()[0]


def get_estado(codigo: str) -> str:
    with sqlite3.connect(app.DB_PATH) as conn:
        row = conn.execute("SELECT estado FROM ubicaciones WHERE codigo = ?", (codigo,)).fetchone()
    return row[0]


def test_upload_valid_csv() -> None:
    content = "codigo,nombre,latitud,longitud\nUBI-001,Uno,-12.04,-77.03\nUBI-002,Dos,40.4,-3.7\n"
    status, data = app.upload_csv(content)

    assert status == 200
    assert data["inserted"] == 2
    assert data["total_errors"] == 0
    assert count_rows() == 2
    assert get_estado("UBI-001") == "cargado"


def test_upload_csv_with_errors() -> None:
    content = (
        "codigo,nombre,latitud,longitud\n"
        "UBI-010,Válido,-12.01,-77.01\n"
        "UBI-011,SinCoords,,\n"
        "UBI-012,LatMala,120,-77.05\n"
    )
    status, data = app.upload_csv(content)

    assert status == 200
    assert data["inserted"] == 1
    assert data["total_errors"] == 2
    assert {err["row"] for err in data["errors"]} == {3, 4}
    assert count_rows() == 1
