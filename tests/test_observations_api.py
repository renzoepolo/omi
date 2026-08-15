"""Tests de API del CRUD de observaciones.

Son los primeros tests que atraviesan el stack HTTP completo: middleware de
`X-Project-Id`, autenticacion, dependencias de scope y persistencia. El resto de
la suite valida schemas de Pydantic o llama a las funciones de ruta directamente,
asi que nada cubria el camino real de un request.
"""

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import Observation, ObservationStatus, ObservationStatusHistory
from tests.conftest import TEST_PASSWORD

PROJECT_1 = 1
PROJECT_2 = 2


def _login(client: TestClient, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(client: TestClient, email: str, project_id: int) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_login(client, email)}",
        "X-Project-Id": str(project_id),
    }


def _ovi_payload() -> dict:
    """Bloque OVI valido segun las reglas de `validate_business_rules`.

    PROCEDENCIA = 1 (sitio web) exige LINK y prohibe las dos fotos.
    """
    return {
        "TIPO_INMUEBLE": 0,
        "ORIGEN_VALOR": 1,
        "SUPERFICIE": 500,
        "UNI_SUP": 0,
        "MONEDA": 1,
        "VALOR_TOTAL": "250000",
        "NOMENCLATURA": "ABC-123",
        "AFECTACION": 2,
        "FRENTE": 10,
        "FORMA": 1,
        "UBIC_CUADRA": 3,
        "TIPO_BARRIO": 2,
        "SIT_JURIDICA": 1,
        "FECHA_VALOR": "2026-02-19",
        "PROCEDENCIA": 1,
        "TELEFONO": None,
        "FOTO_FACHADA": None,
        "FOTO_CARTEL": None,
        "LINK": "https://example.com/aviso",
    }


def _create_payload(project_id: int = PROJECT_1, **overrides) -> dict:
    payload = {
        "project_id": project_id,
        "property_type": "urbano_baldio",
        "status": "cargado",
        "ovi_urbano_baldio": _ovi_payload(),
    }
    payload.update(overrides)
    return payload


def _create(client: TestClient, headers: dict[str, str], **overrides) -> dict:
    response = client.post(
        f"/projects/{PROJECT_1}/observations",
        json=_create_payload(**overrides),
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


# --- Ciclo de vida -----------------------------------------------------------


def test_create_read_update_and_soft_delete(client: TestClient, session_factory) -> None:
    headers = _headers(client, "user@test.com", PROJECT_1)

    created = _create(client, headers)
    observation_id = created["id"]
    assert created["property_type"] == "urbano_baldio"
    assert created["status"] == "cargado"
    # El alta mapea el bloque OVI a las columnas cabecera de la observacion.
    assert created["price"] == "250000.00"
    assert created["currency"] == "USD"
    assert created["surface_unit"] == "m2"

    listed = client.get(f"/projects/{PROJECT_1}/observations", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [observation_id]

    patched = client.patch(
        f"/projects/{PROJECT_1}/observations/{observation_id}",
        json={"status": "revision"},
        headers=headers,
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["status"] == "revision"

    deleted = client.delete(f"/projects/{PROJECT_1}/observations/{observation_id}", headers=headers)
    assert deleted.status_code == 204

    after_delete = client.get(f"/projects/{PROJECT_1}/observations", headers=headers)
    assert after_delete.json() == []

    # El borrado es logico: la fila tiene que seguir existiendo.
    with session_factory() as db:
        observation = db.scalar(select(Observation).where(Observation.id == UUID(observation_id)))
        assert observation is not None
        assert observation.status == ObservationStatus.ELIMINADO
        assert observation.deleted_at is not None


def test_every_status_change_is_recorded_in_history(client: TestClient, session_factory) -> None:
    headers = _headers(client, "user@test.com", PROJECT_1)
    observation_id = _create(client, headers)["id"]

    client.patch(
        f"/projects/{PROJECT_1}/observations/{observation_id}",
        json={"status": "revision"},
        headers=headers,
    )
    client.delete(f"/projects/{PROJECT_1}/observations/{observation_id}", headers=headers)

    with session_factory() as db:
        history = db.scalars(
            select(ObservationStatusHistory)
            .where(ObservationStatusHistory.observation_id == UUID(observation_id))
            .order_by(ObservationStatusHistory.id)
        ).all()

    assert [row.reason for row in history] == ["create", "update", "delete"]
    assert history[0].from_status is None
    assert history[0].to_status == ObservationStatus.CARGADO
    assert history[-1].to_status == ObservationStatus.ELIMINADO


def test_patch_without_status_change_does_not_add_history(
    client: TestClient, session_factory
) -> None:
    headers = _headers(client, "user@test.com", PROJECT_1)
    observation_id = _create(client, headers)["id"]

    response = client.patch(
        f"/projects/{PROJECT_1}/observations/{observation_id}",
        json={"unit_land_value": "1234.50"},
        headers=headers,
    )
    assert response.status_code == 200, response.text

    with session_factory() as db:
        rows = db.scalars(
            select(ObservationStatusHistory).where(
                ObservationStatusHistory.observation_id == UUID(observation_id)
            )
        ).all()

    assert [row.reason for row in rows] == ["create"]


# --- Aislamiento entre proyectos ---------------------------------------------


def test_request_without_project_header_is_rejected(client: TestClient) -> None:
    token = _login(client, "user@test.com")
    response = client.get(
        f"/projects/{PROJECT_1}/observations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing X-Project-Id header"


def test_non_numeric_project_header_is_rejected(client: TestClient) -> None:
    token = _login(client, "user@test.com")
    response = client.get(
        f"/projects/{PROJECT_1}/observations",
        headers={"Authorization": f"Bearer {token}", "X-Project-Id": "proyecto-uno"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "X-Project-Id must be numeric"


def test_user_cannot_scope_into_a_project_they_do_not_belong_to(client: TestClient) -> None:
    # `other@test.com` solo pertenece al proyecto 2.
    headers = _headers(client, "other@test.com", PROJECT_1)
    response = client.get(f"/projects/{PROJECT_1}/observations", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have access to this project"


def test_path_project_must_match_header_scope(client: TestClient) -> None:
    headers = _headers(client, "user@test.com", PROJECT_1)
    response = client.get(f"/projects/{PROJECT_2}/observations", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Project path param does not match active project scope"


def test_body_project_id_must_match_path(client: TestClient) -> None:
    headers = _headers(client, "user@test.com", PROJECT_1)
    response = client.post(
        f"/projects/{PROJECT_1}/observations",
        json=_create_payload(project_id=PROJECT_2),
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "project_id body and path must match"


def test_observations_are_not_visible_across_projects(client: TestClient) -> None:
    owner_headers = _headers(client, "user@test.com", PROJECT_1)
    observation_id = _create(client, owner_headers)["id"]

    outsider_headers = _headers(client, "other@test.com", PROJECT_2)
    listed = client.get(f"/projects/{PROJECT_2}/observations", headers=outsider_headers)
    assert listed.status_code == 200
    assert listed.json() == []

    patched = client.patch(
        f"/projects/{PROJECT_2}/observations/{observation_id}",
        json={"status": "revision"},
        headers=outsider_headers,
    )
    assert patched.status_code == 404


# --- Contrato de `extras` ----------------------------------------------------


def test_extras_keeps_coordinates_and_drops_name_and_description(
    client: TestClient,
) -> None:
    headers = _headers(client, "user@test.com", PROJECT_1)
    created = _create(
        client,
        headers,
        extras={
            "coordinates": [-65.2145, -26.8241],
            "name": "se descarta",
            "description": "tambien se descarta",
            "observaciones": "campo libre que si se conserva",
        },
    )

    extras = created["extras"]
    # `coordinates` es lo que el visor usa para dibujar el punto: perderlo deja
    # la observacion sin ubicacion en el mapa.
    assert extras["coordinates"] == [-65.2145, -26.8241]
    assert extras["observaciones"] == "campo libre que si se conserva"
    assert "name" not in extras
    assert "description" not in extras


def test_unknown_payload_field_is_rejected(client: TestClient) -> None:
    headers = _headers(client, "user@test.com", PROJECT_1)
    response = client.post(
        f"/projects/{PROJECT_1}/observations",
        json=_create_payload(campo_inventado="x"),
        headers=headers,
    )
    # Todos los schemas usan extra="forbid".
    assert response.status_code == 422
