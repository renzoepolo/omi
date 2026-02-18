import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.main import app
from app.api.deps import get_db
from app.models import Base, Project, ProjectRole, User, UserProject

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        user = User(email="user@test.com", hashed_password=get_password_hash("test123"))
        other = User(email="other@test.com", hashed_password=get_password_hash("test123"))
        p1 = Project(name="Project 1")
        p2 = Project(name="Project 2")
        db.add_all([user, other, p1, p2])
        db.flush()
        db.add_all(
            [
                UserProject(user_id=user.id, project_id=p1.id, role=ProjectRole.EDITOR),
                UserProject(user_id=other.id, project_id=p2.id, role=ProjectRole.VIEWER),
            ]
        )
        db.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
