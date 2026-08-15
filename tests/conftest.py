import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import get_password_hash
from app.main import app
from app.models import (
    Base,
    CatalogCurrency,
    CatalogPropertyType,
    CatalogValueOrigin,
    Project,
    ProjectRole,
    User,
    UserProject,
)

TEST_PASSWORD = "test123"


def _seed(db: Session) -> None:
    user = User(email="user@test.com", hashed_password=get_password_hash(TEST_PASSWORD))
    other = User(email="other@test.com", hashed_password=get_password_hash(TEST_PASSWORD))
    super_admin = User(email="super@test.com", hashed_password=get_password_hash(TEST_PASSWORD))
    project_admin = User(email="padmin@test.com", hashed_password=get_password_hash(TEST_PASSWORD))
    p1 = Project(name="Project 1")
    p2 = Project(name="Project 2")
    db.add_all([user, other, super_admin, project_admin, p1, p2])
    db.flush()
    db.add_all(
        [
            UserProject(user_id=user.id, project_id=p1.id, role=ProjectRole.EDITOR),
            UserProject(user_id=other.id, project_id=p2.id, role=ProjectRole.VIEWER),
            UserProject(user_id=super_admin.id, project_id=p1.id, role=ProjectRole.SUPER_ADMIN),
            UserProject(user_id=project_admin.id, project_id=p1.id, role=ProjectRole.PROJECT_ADMIN),
        ]
    )

    # Los catalogos son obligatorios para dar de alta una observacion: la API
    # habla por `code` y traduce a `id` contra estas tablas. Sin las filas, todo
    # POST /observations responde 400 "Invalid catalog code".
    db.add_all(
        [
            CatalogPropertyType(code="urbano_baldio", label="Urbano baldio", sort_order=1),
            CatalogPropertyType(code="urbano_edificado", label="Urbano edificado", sort_order=2),
            CatalogPropertyType(code="rural", label="Rural", sort_order=3),
            CatalogCurrency(code="ARS", label="Pesos", sort_order=1),
            CatalogCurrency(code="USD", label="Dolares", sort_order=2),
            CatalogValueOrigin(code="oferta", label="Oferta", sort_order=1),
            CatalogValueOrigin(code="venta", label="Venta", sort_order=2),
        ]
    )
    db.commit()


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        _seed(db)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def session_factory(engine):
    """Sesiones contra la misma base en memoria que usa el `client`.

    Sirve para verificar efectos que la API no devuelve en la respuesta, como el
    borrado logico o las filas de `observation_status_history`.
    """
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


@pytest.fixture()
def client(session_factory) -> TestClient:
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
