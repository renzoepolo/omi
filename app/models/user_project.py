import enum

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProjectRole(str, enum.Enum):
    SUPER_ADMIN = "SuperAdmin"
    PROJECT_ADMIN = "ProjectAdmin"
    EDITOR = "Editor"
    VIEWER = "Viewer"


class UserProject(Base):
    __tablename__ = "user_projects"
    __table_args__ = (UniqueConstraint("user_id", "project_id", name="uq_user_project"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[ProjectRole] = mapped_column(
        Enum(
            ProjectRole,
            name="project_role",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=ProjectRole.VIEWER,
    )

    user = relationship("User", back_populates="projects")
    project = relationship("Project", back_populates="users")
