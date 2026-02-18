import csv
import io
import json
import sqlite3
from contextlib import contextmanager
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

DB_PATH = Path("/tmp/omi_bulk_load.db")
REQUIRED_FIELDS = ["codigo", "nombre", "latitud", "longitud"]


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ubicaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                latitud REAL NOT NULL,
                longitud REAL NOT NULL,
                estado TEXT NOT NULL
            )
            """
        )
        conn.commit()


@contextmanager
def transactional_connection() -> Any:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("BEGIN")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def validate_wgs84(latitud: str, longitud: str) -> tuple[float | None, float | None, str | None]:
    try:
        lat = float(latitud)
        lon = float(longitud)
    except (TypeError, ValueError):
        return None, None, "latitud/longitud deben ser numéricas"

    if not (-90 <= lat <= 90):
        return None, None, "latitud fuera de rango WGS84 (-90 a 90)"
    if not (-180 <= lon <= 180):
        return None, None, "longitud fuera de rango WGS84 (-180 a 180)"
    return lat, lon, None


def download_template_csv() -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=REQUIRED_FIELDS)
    writer.writeheader()
    writer.writerow(
        {
            "codigo": "UBI-001",
            "nombre": "Punto de referencia",
            "latitud": "-12.0464",
            "longitud": "-77.0428",
        }
    )
    return output.getvalue()


def upload_csv(payload: str) -> tuple[int, dict[str, Any]]:
    try:
        reader = csv.DictReader(io.StringIO(payload))
    except csv.Error:
        return HTTPStatus.BAD_REQUEST, {"detail": "CSV inválido"}

    if not reader.fieldnames:
        return HTTPStatus.BAD_REQUEST, {"detail": "CSV sin encabezados"}

    missing_headers = [header for header in REQUIRED_FIELDS if header not in reader.fieldnames]
    if missing_headers:
        return HTTPStatus.BAD_REQUEST, {
            "critical_error": True,
            "message": "Faltan columnas obligatorias en el encabezado",
            "missing_headers": missing_headers,
        }

    errors: list[dict[str, Any]] = []
    inserted = 0
    seen_codes: set[str] = set()

    try:
        with transactional_connection() as conn:
            for row_number, row in enumerate(reader, start=2):
                missing_fields = [f for f in REQUIRED_FIELDS if not (row.get(f) or "").strip()]
                if missing_fields:
                    errors.append(
                        {
                            "row": row_number,
                            "error": "campos obligatorios faltantes",
                            "fields": missing_fields,
                        }
                    )
                    continue

                codigo = row["codigo"].strip()
                nombre = row["nombre"].strip()

                if codigo in seen_codes:
                    return HTTPStatus.BAD_REQUEST, {
                        "critical_error": True,
                        "row": row_number,
                        "message": f"codigo duplicado en archivo: {codigo}",
                    }
                seen_codes.add(codigo)

                lat, lon, coord_error = validate_wgs84(row["latitud"], row["longitud"])
                if coord_error:
                    errors.append({"row": row_number, "error": coord_error})
                    continue

                try:
                    conn.execute(
                        """
                        INSERT INTO ubicaciones (codigo, nombre, latitud, longitud, estado)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (codigo, nombre, lat, lon, "cargado"),
                    )
                    inserted += 1
                except sqlite3.IntegrityError as exc:
                    return HTTPStatus.BAD_REQUEST, {
                        "critical_error": True,
                        "row": row_number,
                        "message": "Error de integridad al insertar",
                        "db_error": str(exc),
                    }
    except Exception as exc:
        return HTTPStatus.INTERNAL_SERVER_ERROR, {"detail": f"Error interno: {exc}"}

    return HTTPStatus.OK, {
        "inserted": inserted,
        "errors": errors,
        "total_errors": len(errors),
    }


class OmiHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/cargas/plantilla.csv":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = download_template_csv().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/cargas/csv":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_len = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_len)
        try:
            payload = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            status, data = HTTPStatus.BAD_REQUEST, {"detail": "El archivo no es UTF-8 válido"}
        else:
            status, data = upload_csv(payload)

        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    init_db()
    server = ThreadingHTTPServer((host, port), OmiHandler)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
