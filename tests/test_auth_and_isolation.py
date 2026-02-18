import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_project_membership
from app.api.routes.auth import login
from app.core.security import decode_token, get_password_hash
from app.models import Base, Project, ProjectRole, User, UserProject
from app.schemas.auth import LoginRequest


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        user = User(email="user@test.com", hashed_password=get_password_hash("test123"))
        other = User(email="other@test.com", hashed_password=get_password_hash("test123"))
        p1 = Project(name="Project 1")
        p2 = Project(name="Project 2")
        session.add_all([user, other, p1, p2])
        session.flush()
        session.add_all(
            [
                UserProject(user_id=user.id, project_id=p1.id, role=ProjectRole.EDITOR),
                UserProject(user_id=other.id, project_id=p2.id, role=ProjectRole.VIEWER),
            ]
        )
        session.commit()
        yield session


def test_login_success(db: Session) -> None:
    token = login(LoginRequest(email="user@test.com", password="test123"), db=db)
    payload = decode_token(token.access_token)

    assert token.token_type == "bearer"
    assert token.access_token
    assert payload is not None
    assert payload["sub"]


def test_access_project_allowed(db: Session) -> None:
    user = db.scalar(select(User).where(User.email == "user@test.com"))
    assert user is not None

    membership = get_project_membership(db=db, current_user=user, project_id=1)
    assert membership.project_id == 1


def test_project_access_denied_between_projects(db: Session) -> None:
    user = db.scalar(select(User).where(User.email == "user@test.com"))
    assert user is not None

    with pytest.raises(HTTPException) as exc:
        get_project_membership(db=db, current_user=user, project_id=2)
    assert exc.value.status_code == 403
