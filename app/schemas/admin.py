from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user_project import ProjectRole


class LayerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    geoserver_workspace: str = Field(min_length=1, max_length=255)
    geoserver_layer_name: str = Field(min_length=1, max_length=255)
    style_name: str | None = Field(default=None, min_length=1, max_length=255)
    type: str = Field(pattern="^WMS$")
    default_visible: bool = True
    z_index: int = 0


class LayerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    geoserver_workspace: str | None = Field(default=None, min_length=1, max_length=255)
    geoserver_layer_name: str | None = Field(default=None, min_length=1, max_length=255)
    style_name: str | None = Field(default=None, min_length=1, max_length=255)
    type: str | None = Field(default=None, pattern="^WMS$")
    default_visible: bool | None = None
    z_index: int | None = None


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    default_map_center: list[float] = Field(default_factory=lambda: [-77.0428, -12.0464], min_length=2, max_length=2)
    default_zoom: int = 13

    @field_validator("default_zoom", mode="before")
    @classmethod
    def normalize_default_zoom(cls, value):
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return value


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    default_map_center: list[float] | None = Field(default=None, min_length=2, max_length=2)
    default_zoom: int | None = None

    @field_validator("default_zoom", mode="before")
    @classmethod
    def normalize_default_zoom(cls, value):
        if value is None:
            return None
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return value


class FormFieldDefinitionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_key: str = Field(min_length=1, max_length=128)
    label: str = Field(min_length=1, max_length=255)
    field_type: str = Field(min_length=1, max_length=64)
    required: bool = False
    order_index: int = 0
    config: dict = Field(default_factory=dict)


class ProjectLayerAttach(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layer_id: int = Field(gt=0)
    available_override: bool | None = None
    visible_override: bool | None = None
    z_index_override: int | None = None


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=255)
    is_active: bool = True


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str | None = Field(default=None, min_length=3, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=255)
    is_active: bool | None = None


class UserProjectAssign(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: int = Field(gt=0)
    role: ProjectRole


class AdminAuditRead(BaseModel):
    id: int
    actor_user_id: int
    action: str
    target_type: str
    target_id: str
    project_id: int | None
    ip_address: str | None
    user_agent: str | None
    details: dict
    created_at: datetime
