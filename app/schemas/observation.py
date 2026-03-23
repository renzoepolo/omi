import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.core.ovi_enums import get_ovi_allowed_codes


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


class OviUrbanoBaldioPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    TIPO_INMUEBLE: int
    ORIGEN_VALOR: int
    SUPERFICIE: int = Field(ge=0)
    UNI_SUP: int
    MONEDA: int
    VALOR_TOTAL: Decimal = Field(ge=0)
    NOMENCLATURA: str = Field(min_length=1, max_length=255)
    AFECTACION: int
    FRENTE: int
    FORMA: int
    UBIC_CUADRA: int
    TIPO_BARRIO: int
    SIT_JURIDICA: int
    FECHA_VALOR: date
    PROCEDENCIA: int
    TELEFONO: str | None = Field(default=None, max_length=255)
    FOTO_FACHADA: str | None = Field(default=None, max_length=1024)
    FOTO_CARTEL: str | None = Field(default=None, max_length=1024)
    LINK: str | None = Field(default=None, max_length=1024)

    @model_validator(mode="after")
    def validate_business_rules(self) -> "OviUrbanoBaldioPayload":
        allowed = get_ovi_allowed_codes()
        enum_fields = (
            "TIPO_INMUEBLE",
            "ORIGEN_VALOR",
            "UNI_SUP",
            "MONEDA",
            "AFECTACION",
            "FORMA",
            "UBIC_CUADRA",
            "TIPO_BARRIO",
            "SIT_JURIDICA",
            "PROCEDENCIA",
        )
        for field_name in enum_fields:
            value = int(getattr(self, field_name))
            if value not in allowed[field_name]:
                raise ValueError(f"{field_name} has invalid code {value}")

        if self.TIPO_INMUEBLE != 0:
            raise ValueError("TIPO_INMUEBLE must be 0 for urbano baldio")
        if self.UNI_SUP != 0:
            raise ValueError("UNI_SUP must be 0 for urbano baldio")
        if self.PROCEDENCIA == 0:
            if not self.FOTO_FACHADA or not self.FOTO_CARTEL:
                raise ValueError("FOTO_FACHADA and FOTO_CARTEL are required when PROCEDENCIA = 0")
            if self.LINK:
                raise ValueError("LINK must be null when PROCEDENCIA = 0")
        elif self.PROCEDENCIA == 1:
            if not self.LINK:
                raise ValueError("LINK is required when PROCEDENCIA = 1")
            if self.FOTO_FACHADA or self.FOTO_CARTEL:
                raise ValueError("FOTO_FACHADA and FOTO_CARTEL must be null when PROCEDENCIA = 1")
        else:
            if self.FOTO_FACHADA or self.FOTO_CARTEL or self.LINK:
                raise ValueError("FOTO_FACHADA, FOTO_CARTEL and LINK must be null when PROCEDENCIA is neither 0 nor 1")
        return self


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
    ovi_urbano_baldio: OviUrbanoBaldioPayload | None = None

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
        if self.property_type == PropertyTypeEnum.URBANO_BALDIO and self.ovi_urbano_baldio is None:
            raise ValueError("ovi_urbano_baldio payload is required for urbano_baldio")
        if self.property_type != PropertyTypeEnum.URBANO_BALDIO and self.ovi_urbano_baldio is not None:
            raise ValueError("ovi_urbano_baldio payload is only allowed for urbano_baldio")
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
    ovi_urbano_baldio: OviUrbanoBaldioPayload | None = None

    @model_validator(mode="after")
    def validate_price_currency_pair(self) -> "ObservationUpdate":
        # Pair validation only if one of the fields is present in update payload.
        if self.price is not None and self.currency is None:
            raise ValueError("currency is required when price is provided")
        if self.currency is not None and self.price is None:
            raise ValueError("price is required when currency is provided")
        if self.ovi_urbano_baldio is not None and self.property_type not in (
            None,
            PropertyTypeEnum.URBANO_BALDIO,
        ):
            raise ValueError("ovi_urbano_baldio payload is only allowed for urbano_baldio")
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
    ovi_urbano_baldio: OviUrbanoBaldioPayload | None = None
    created_at: datetime
    updated_at: datetime
