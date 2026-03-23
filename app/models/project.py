from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_center_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    default_center_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    default_zoom: Mapped[int] = mapped_column(Integer, nullable=False, default=13)

    users = relationship("UserProject", back_populates="project", cascade="all, delete-orphan")
    project_layers = relationship("ProjectLayer", back_populates="project", cascade="all, delete-orphan")
    form_field_definitions = relationship(
        "FormFieldDefinition", back_populates="project", cascade="all, delete-orphan"
    )
