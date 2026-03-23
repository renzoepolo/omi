import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app.api.deps import get_admin_membership
from app.api.routes.admin import _ensure_project_scope, admin_create_project, admin_update_project
from app.core.security import get_password_hash
from app.models import AdminAuditLog, Base, Project, ProjectRole, User, UserProject
from app.schemas.admin import ProjectCreate, ProjectUpdate


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
        super_admin = User(email="super@test.com", hashed_password=get_password_hash("test123"))
        project_admin = User(email="padmin@test.com", hashed_password=get_password_hash("test123"))
        editor = User(email="editor@test.com", hashed_password=get_password_hash("test123"))
        p1 = Project(name="Project 1")
        p2 = Project(name="Project 2")
        session.add_all([super_admin, project_admin, editor, p1, p2])
        session.flush()
        session.add_all(
            [
                UserProject(user_id=super_admin.id, project_id=p1.id, role=ProjectRole.SUPER_ADMIN),
                UserProject(user_id=project_admin.id, project_id=p1.id, role=ProjectRole.PROJECT_ADMIN),
                UserProject(user_id=editor.id, project_id=p1.id, role=ProjectRole.EDITOR),
            ]
        )
        session.commit()
        yield session


def _request(user_agent: str = "pytest-agent") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/admin/projects",
        "headers": [(b"user-agent", user_agent.encode("utf-8"))],
        "client": ("127.0.0.1", 5000),
    }
    return Request(scope)


def test_get_admin_membership_allows_super_and_project_admin(db: Session) -> None:
    super_membership = db.scalar(
        select(UserProject).where(UserProject.role == ProjectRole.SUPER_ADMIN)
    )
    project_admin_membership = db.scalar(
        select(UserProject).where(UserProject.role == ProjectRole.PROJECT_ADMIN)
    )
    assert super_membership is not None
    assert project_admin_membership is not None

    assert get_admin_membership(super_membership).role == ProjectRole.SUPER_ADMIN
    assert get_admin_membership(project_admin_membership).role == ProjectRole.PROJECT_ADMIN


def test_get_admin_membership_denies_non_admin(db: Session) -> None:
    editor_membership = db.scalar(select(UserProject).where(UserProject.role == ProjectRole.EDITOR))
    assert editor_membership is not None

    with pytest.raises(HTTPException) as exc:
        get_admin_membership(editor_membership)
    assert exc.value.status_code == 403


def test_project_admin_scope_enforced(db: Session) -> None:
    project_admin_membership = db.scalar(
        select(UserProject).where(UserProject.role == ProjectRole.PROJECT_ADMIN)
    )
    assert project_admin_membership is not None

    _ensure_project_scope(project_admin_membership, 1)

    with pytest.raises(HTTPException) as exc:
        _ensure_project_scope(project_admin_membership, 2)
    assert exc.value.status_code == 403


def test_only_super_admin_can_create_project(db: Session) -> None:
    super_membership = db.scalar(select(UserProject).where(UserProject.role == ProjectRole.SUPER_ADMIN))
    project_admin_membership = db.scalar(
        select(UserProject).where(UserProject.role == ProjectRole.PROJECT_ADMIN)
    )
    super_user = db.scalar(select(User).where(User.email == "super@test.com"))
    project_admin_user = db.scalar(select(User).where(User.email == "padmin@test.com"))
    assert super_membership and project_admin_membership and super_user and project_admin_user

    result = admin_create_project(
        payload=ProjectCreate(name="Project 3", description="new", default_map_center=[-60.0, -30.0], default_zoom=10),
        request=_request("audit-super-agent"),
        db=db,
        current_user=super_user,
        admin_membership=super_membership,
    )
    assert result["id"]

    with pytest.raises(HTTPException) as exc:
        admin_create_project(
            payload=ProjectCreate(
                name="Project 4",
                description="forbidden",
                default_map_center=[-60.0, -30.0],
                default_zoom=10,
            ),
            request=_request("audit-project-admin"),
            db=db,
            current_user=project_admin_user,
            admin_membership=project_admin_membership,
        )
    assert exc.value.status_code == 403


def test_create_project_rejects_existing_name_case_insensitive(db: Session) -> None:
    super_membership = db.scalar(select(UserProject).where(UserProject.role == ProjectRole.SUPER_ADMIN))
    super_user = db.scalar(select(User).where(User.email == "super@test.com"))
    assert super_membership and super_user

    with pytest.raises(HTTPException) as exc:
        admin_create_project(
            payload=ProjectCreate(
                name="  project 1  ",
                description="dup",
                default_map_center=[-60.0, -30.0],
                default_zoom=10,
            ),
            request=_request("dup-name-agent"),
            db=db,
            current_user=super_user,
            admin_membership=super_membership,
        )
    assert exc.value.status_code == 409


def test_admin_audit_is_saved_with_ip_and_user_agent(db: Session) -> None:
    super_membership = db.scalar(select(UserProject).where(UserProject.role == ProjectRole.SUPER_ADMIN))
    super_user = db.scalar(select(User).where(User.email == "super@test.com"))
    assert super_membership and super_user

    response = admin_update_project(
        project_id=1,
        payload=ProjectUpdate(description="audit update"),
        request=_request("audit-test-agent"),
        db=db,
        current_user=super_user,
        admin_membership=super_membership,
    )
    assert response["ok"] is True

    latest_audit = db.scalar(select(AdminAuditLog).order_by(AdminAuditLog.id.desc()))
    assert latest_audit is not None
    assert latest_audit.ip_address == "127.0.0.1"
    assert latest_audit.user_agent == "audit-test-agent"


def test_project_zoom_is_normalized_from_float_in_schema() -> None:
    created = ProjectCreate(
        name="Project zoom",
        description="zoom float",
        default_map_center=[-60.0, -30.0],
        default_zoom=6.7,
    )
    updated = ProjectUpdate(default_zoom=8.2)
    assert created.default_zoom == 7
    assert updated.default_zoom == 8
