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

    @model_validator(mode="after")
    def validate_price_currency_pair(self) -> "ObservationBase":
        if self.price is not None and self.currency is None:
            raise ValueError("currency is required when price is provided")
        if self.currency is not None and self.price is None:
            raise ValueError("price is required when currency is provided")
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
    external_uuid: uuid.UUID | None = None
    legacy_fid: int | None = None
    extras: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
