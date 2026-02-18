import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ObservationStatusEnum(str, Enum):
    CARGADO = "cargado"
    POSICIONADO = "posicionado"
    REVISION = "revision"
    COMPLETADO = "completado"
    OUTLIER = "outlier"
    ELIMINADO = "eliminado"


class PropertyTypeEnum(str, Enum):
    URBANO_BALDIO = "urbano_baldio"
    URBANO_EDIFICADO = "urbano_edificado"
    RURAL = "rural"


class CurrencyEnum(str, Enum):
    ARS = "ARS"
    USD = "USD"


class ObservationLocationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    padron: str | None = Field(default=None, max_length=255)
    neighborhood_type_code: str | None = Field(default=None, max_length=64)
    shape_type_code: str | None = Field(default=None, max_length=64)
    block_position_code: str | None = Field(default=None, max_length=64)
    legal_status_code: str | None = Field(default=None, max_length=64)
    affectation_code: str | None = Field(default=None, max_length=64)


class ObservationBuildingPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    built_surface_total: Decimal | None = Field(default=None, ge=0)
    warehouse_surface: Decimal | None = Field(default=None, ge=0)
    front_meters: Decimal | None = Field(default=None, ge=0)
    conservation_state_code: str | None = Field(default=None, max_length=64)
    destination_code: str | None = Field(default=None, max_length=64)
    construction_category_code: str | None = Field(default=None, max_length=64)
    bedrooms_count: int | None = Field(default=None, ge=0)
    bathrooms_count: int | None = Field(default=None, ge=0)
    garage_count: int | None = Field(default=None, ge=0)
    floors_count: int | None = Field(default=None, ge=0)
    has_pool: bool | None = None
    antiquity_year: int | None = Field(default=None, ge=1800, le=2200)


class ObservationRuralPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    main_use_code: str | None = Field(default=None, max_length=64)
    sugarcane_surface: Decimal | None = Field(default=None, ge=0)
    citrus_surface: Decimal | None = Field(default=None, ge=0)
    grains_surface: Decimal | None = Field(default=None, ge=0)
    forest_surface: Decimal | None = Field(default=None, ge=0)
    other_crops_surface: Decimal | None = Field(default=None, ge=0)
    has_irrigation: bool | None = None
    irrigation_type_code: str | None = Field(default=None, max_length=64)
    irrigated_surface: Decimal | None = Field(default=None, ge=0)
    irrigation_concession_type_code: str | None = Field(default=None, max_length=64)
    has_extraordinary_improvements: bool | None = None
    has_rural_improvements: bool | None = None


class ObservationBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: int = Field(gt=0)
    property_type: PropertyTypeEnum
    status: ObservationStatusEnum = ObservationStatusEnum.CARGADO
    price: Decimal | None = Field(default=None, ge=0)
    currency: CurrencyEnum | None = None
    valuation_date: date | None = None
    unit_land_value: Decimal | None = Field(default=None, ge=0)
    surface_total: Decimal | None = Field(default=None, ge=0)
    surface_unit: str = Field(default="m2", min_length=1, max_length=16)
    value_origin_code: str | None = Field(default=None, max_length=64)
    external_uuid: uuid.UUID | None = None
    legacy_fid: int | None = None
    extras: dict = Field(default_factory=dict)
    location: ObservationLocationPayload | None = None
    building: ObservationBuildingPayload | None = None
    rural: ObservationRuralPayload | None = None

    @model_validator(mode="after")
    def validate_price_currency_pair(self) -> "ObservationBase":
        if self.price is not None and self.currency is None:
            raise ValueError("currency is required when price is provided")
        if self.currency is not None and self.price is None:
            raise ValueError("price is required when currency is provided")
        return self

    @model_validator(mode="after")
    def validate_payload_by_property_type(self) -> "ObservationBase":
        if self.property_type == PropertyTypeEnum.RURAL and self.building is not None:
            raise ValueError("building payload is not allowed for rural property_type")
        if self.property_type in (
            PropertyTypeEnum.URBANO_BALDIO,
            PropertyTypeEnum.URBANO_EDIFICADO,
        ) and self.rural is not None:
            raise ValueError("rural payload is not allowed for urban property_type")
        return self


class ObservationCreate(ObservationBase):
    pass


class ObservationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_type: PropertyTypeEnum | None = None
    status: ObservationStatusEnum | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: CurrencyEnum | None = None
    valuation_date: date | None = None
    unit_land_value: Decimal | None = Field(default=None, ge=0)
    surface_total: Decimal | None = Field(default=None, ge=0)
    surface_unit: str | None = Field(default=None, min_length=1, max_length=16)
    value_origin_code: str | None = Field(default=None, max_length=64)
    extras: dict | None = None
    location: ObservationLocationPayload | None = None
    building: ObservationBuildingPayload | None = None
    rural: ObservationRuralPayload | None = None

    @model_validator(mode="after")
    def validate_price_currency_pair(self) -> "ObservationUpdate":
        # Pair validation only if one of the fields is present in update payload.
        if self.price is not None and self.currency is None:
            raise ValueError("currency is required when price is provided")
        if self.currency is not None and self.price is None:
            raise ValueError("price is required when currency is provided")
        return self


class ObservationRead(BaseModel):
    id: uuid.UUID
    project_id: int
    property_type: PropertyTypeEnum
    status: ObservationStatusEnum
    price: Decimal | None = None
    currency: CurrencyEnum | None = None
    valuation_date: date | None = None
    unit_land_value: Decimal | None = None
    surface_total: Decimal | None = None
    surface_unit: str
    value_origin_code: str | None = None
    external_uuid: uuid.UUID | None = None
    legacy_fid: int | None = None
    extras: dict = Field(default_factory=dict)
    location: ObservationLocationPayload | None = None
    building: ObservationBuildingPayload | None = None
    rural: ObservationRuralPayload | None = None
    created_at: datetime
    updated_at: datetime
