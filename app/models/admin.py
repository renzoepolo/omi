import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LayerType(str, enum.Enum):
    WMS = "WMS"
    WFS = "WFS"


class Layer(Base):
    __tablename__ = "layers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    geoserver_workspace: Mapped[str] = mapped_column(String(255), nullable=False)
    geoserver_layer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    style_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[LayerType] = mapped_column(
        Enum(
            LayerType,
            name="layer_type",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    default_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    projects = relationship("ProjectLayer", back_populates="layer", cascade="all, delete-orphan")


class ProjectLayer(Base):
    __tablename__ = "project_layers"
    __table_args__ = (UniqueConstraint("project_id", "layer_id", name="uq_project_layer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    layer_id: Mapped[int] = mapped_column(ForeignKey("layers.id", ondelete="CASCADE"), nullable=False)
    available_override: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    visible_override: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    z_index_override: Mapped[int | None] = mapped_column(Integer, nullable=True)

    project = relationship("Project", back_populates="project_layers")
    layer = relationship("Layer", back_populates="projects")


class FormFieldDefinition(Base):
    __tablename__ = "form_field_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    field_key: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(64), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    project = relationship("Project", back_populates="form_field_definitions")


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(128), nullable=False)
    target_id: Mapped[str] = mapped_column(String(128), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
