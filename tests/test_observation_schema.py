from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.observation import ObservationCreate, ObservationStatusEnum, PropertyTypeEnum


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
