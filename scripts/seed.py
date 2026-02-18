from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Project, ProjectRole, User, UserProject


def run() -> None:
    engine = create_engine(settings.database_url, future=True)
    with Session(engine) as db:
        admin = db.scalar(select(User).where(User.email == "admin@omi.local"))
        if not admin:
            admin = User(email="admin@omi.local", hashed_password=get_password_hash("admin123"))
            db.add(admin)

        ana = db.scalar(select(User).where(User.email == "ana@omi.local"))
        if not ana:
            ana = User(email="ana@omi.local", hashed_password=get_password_hash("ana123"))
            db.add(ana)

        p1 = db.scalar(select(Project).where(Project.name == "Proyecto A"))
        if not p1:
            p1 = Project(name="Proyecto A")
            db.add(p1)

        p2 = db.scalar(select(Project).where(Project.name == "Proyecto B"))
        if not p2:
            p2 = Project(name="Proyecto B")
            db.add(p2)

        db.flush()

        links = {
            (admin.id, p1.id): ProjectRole.SUPER_ADMIN,
            (admin.id, p2.id): ProjectRole.PROJECT_ADMIN,
            (ana.id, p1.id): ProjectRole.EDITOR,
        }

        for (user_id, project_id), role in links.items():
            exists = db.scalar(
                select(UserProject).where(
                    UserProject.user_id == user_id,
                    UserProject.project_id == project_id,
                )
            )
            if not exists:
                db.add(UserProject(user_id=user_id, project_id=project_id, role=role))

        db.commit()


if __name__ == "__main__":
    run()
