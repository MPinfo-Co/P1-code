import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.user import Role, User, UserRole

TEST_DATABASE_URL = "sqlite:///:memory:"

_SEED_TABLES = [User.__table__, Role.__table__, UserRole.__table__]


@pytest.fixture(scope="function")
def engine():
    _engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(bind=_engine, checkfirst=True)
    Role.__table__.create(bind=_engine, checkfirst=True)
    UserRole.__table__.create(bind=_engine, checkfirst=True)
    yield _engine
    UserRole.__table__.drop(bind=_engine, checkfirst=True)
    User.__table__.drop(bind=_engine, checkfirst=True)
    Role.__table__.drop(bind=_engine, checkfirst=True)


@pytest.fixture(scope="function")
def client(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
