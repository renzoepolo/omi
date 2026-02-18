import enum
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Uuid, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ObservationStatus(str, enum.Enum):
    CARGADO = "cargado"
    POSICIONADO = "posicionado"
    REVISION = "revision"
    COMPLETADO = "completado"
    OUTLIER = "outlier"
    ELIMINADO = "eliminado"


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint("project_id", "external_uuid", name="uq_observations_project_external_uuid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    external_uuid: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    legacy_fid: Mapped[int | None] = mapped_column(nullable=True)

    property_type_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_property_type.id", ondelete="RESTRICT"), nullable=False
    )
    value_origin_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_value_origin.id", ondelete="RESTRICT"), nullable=True
    )
    currency_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_currency.id", ondelete="RESTRICT"), nullable=True
    )

    market_value_total: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    unit_land_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    valuation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    surface_total: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    surface_unit: Mapped[str] = mapped_column(String(16), nullable=False, default="m2")

    status: Mapped[ObservationStatus] = mapped_column(
        Enum(
            ObservationStatus,
            name="observation_status",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=ObservationStatus.CARGADO,
        index=True,
    )
    is_outlier: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    extras: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )

    status_history = relationship(
        "ObservationStatusHistory",
        back_populates="observation",
        cascade="all, delete-orphan",
    )


class ObservationStatusHistory(Base):
    __tablename__ = "observation_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    observation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("observations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[ObservationStatus | None] = mapped_column(
        Enum(
            ObservationStatus,
            name="observation_status",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=True,
    )
    to_status: Mapped[ObservationStatus] = mapped_column(
        Enum(
            ObservationStatus,
            name="observation_status",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    observation = relationship("Observation", back_populates="status_history")
