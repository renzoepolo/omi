from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.observation import ObservationCreate, ObservationStatusEnum, PropertyTypeEnum


def _valid_ovi_payload() -> dict:
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


def _build_urbano_baldio_payload(ovi: dict) -> ObservationCreate:
    return ObservationCreate(
        project_id=1,
        property_type="urbano_baldio",
        status="cargado",
        ovi_urbano_baldio=ovi,
    )


def test_observation_create_accepts_valid_payload() -> None:
    payload = ObservationCreate(
        project_id=1,
        property_type=PropertyTypeEnum.URBANO_EDIFICADO,
        status=ObservationStatusEnum.CARGADO,
        price=Decimal("123456.78"),
        currency="USD",
        valuation_date=date(2026, 2, 18),
        surface_total=Decimal("230.50"),
        surface_unit="m2",
        value_origin_code="oferta",
    )
    assert payload.currency == "USD"
    assert payload.price == Decimal("123456.78")


def test_observation_create_requires_currency_when_price_present() -> None:
    with pytest.raises(ValidationError):
        ObservationCreate(
            project_id=1,
            property_type="urbano_baldio",
            price=Decimal("1000"),
        )


def test_observation_create_rejects_unknown_property_type() -> None:
    with pytest.raises(ValidationError):
        ObservationCreate(
            project_id=1,
            property_type="ph",
            status="cargado",
        )


def test_observation_create_rejects_rural_payload_for_urban_type() -> None:
    with pytest.raises(ValidationError):
        ObservationCreate(
            project_id=1,
            property_type="urbano_baldio",
            rural={"main_use_code": "agricola"},
        )


def test_observation_create_rejects_building_payload_for_rural_type() -> None:
    with pytest.raises(ValidationError):
        ObservationCreate(
            project_id=1,
            property_type="rural",
            building={"bedrooms_count": 2},
        )


def test_observation_create_requires_ovi_for_urbano_baldio() -> None:
    with pytest.raises(ValidationError):
        ObservationCreate(
            project_id=1,
            property_type="urbano_baldio",
            status="cargado",
        )


def test_observation_create_accepts_ovi_urbano_baldio_with_procedencia_web() -> None:
    payload = _build_urbano_baldio_payload(_valid_ovi_payload())
    assert payload.ovi_urbano_baldio is not None
    assert payload.ovi_urbano_baldio.PROCEDENCIA == 1


def test_observation_create_rejects_ovi_link_when_procedencia_campo() -> None:
    invalid = _valid_ovi_payload()
    invalid["PROCEDENCIA"] = 0
    invalid["FOTO_FACHADA"] = "a.jpg"
    invalid["FOTO_CARTEL"] = "b.jpg"
    invalid["LINK"] = "https://example.com/aviso"
    with pytest.raises(ValidationError):
        _build_urbano_baldio_payload(invalid)


@pytest.mark.parametrize(
    "field,valid_value,invalid_value",
    [
        ("TIPO_INMUEBLE", 0, 99),
        ("ORIGEN_VALOR", 0, 99),
        ("UNI_SUP", 0, 99),
        ("MONEDA", 0, 99),
        ("AFECTACION", 0, 99),
        ("FORMA", 0, 99),
        ("UBIC_CUADRA", 0, 99),
        ("TIPO_BARRIO", 0, 99),
        ("SIT_JURIDICA", 0, 99),
        ("PROCEDENCIA", 1, 99),
    ],
)
def test_ovi_enums_accept_valid_and_reject_invalid(field: str, valid_value: int, invalid_value: int) -> None:
    valid = _valid_ovi_payload()
    valid[field] = valid_value
    if field == "PROCEDENCIA":
        valid["LINK"] = "https://example.com/ok"
        valid["FOTO_FACHADA"] = None
        valid["FOTO_CARTEL"] = None
    payload = _build_urbano_baldio_payload(valid)
    assert payload.ovi_urbano_baldio is not None

    invalid = _valid_ovi_payload()
    invalid[field] = invalid_value
    with pytest.raises(ValidationError):
        _build_urbano_baldio_payload(invalid)


def test_procedencia_conditional_rules() -> None:
    campo_ok = _valid_ovi_payload()
    campo_ok["PROCEDENCIA"] = 0
    campo_ok["FOTO_FACHADA"] = "fachada.jpg"
    campo_ok["FOTO_CARTEL"] = "cartel.jpg"
    campo_ok["LINK"] = None
    assert _build_urbano_baldio_payload(campo_ok).ovi_urbano_baldio is not None

    web_ok = _valid_ovi_payload()
    web_ok["PROCEDENCIA"] = 1
    web_ok["FOTO_FACHADA"] = None
    web_ok["FOTO_CARTEL"] = None
    web_ok["LINK"] = "https://example.com/web"
    assert _build_urbano_baldio_payload(web_ok).ovi_urbano_baldio is not None

    agente_invalid = _valid_ovi_payload()
    agente_invalid["PROCEDENCIA"] = 2
    agente_invalid["FOTO_FACHADA"] = "x.jpg"
    agente_invalid["FOTO_CARTEL"] = None
    agente_invalid["LINK"] = None
    with pytest.raises(ValidationError):
        _build_urbano_baldio_payload(agente_invalid)
