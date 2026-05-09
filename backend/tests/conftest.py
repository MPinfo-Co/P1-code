import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.connector import get_db
from app.main import app
from app.db.models.analysis import ChunkResult, DailyAnalysis, LogBatch
from app.db.models.events import SecurityEvent
from app.db.models.fn_expert_setting import ExpertSetting
from app.db.models.fn_tool import Tool, ToolBodyParam
from app.db.models.function_access import (
    FunctionItems as Function,
    FunctionFolder,
    RoleFunction,
)
from app.db.models.user_role import Role, TokenBlacklist, User, UserRole


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    """Render JSONB as JSON on SQLite so tb_chunk_results can be created in tests."""
    return "JSON"


@compiles(BigInteger, "sqlite")
def _compile_bigint_sqlite(element, compiler, **kw):
    """Render BigInteger as INTEGER on SQLite so PK autoincrement (ROWID) works."""
    return "INTEGER"


TEST_DATABASE_URL = "sqlite:///:memory:"

_SEED_TABLES = [
    User.__table__,
    Role.__table__,
    UserRole.__table__,
    TokenBlacklist.__table__,
    FunctionFolder.__table__,
    Function.__table__,
    RoleFunction.__table__,
    Tool.__table__,
    ToolBodyParam.__table__,
    ExpertSetting.__table__,
    LogBatch.__table__,
    ChunkResult.__table__,
    DailyAnalysis.__table__,
    SecurityEvent.__table__,
]


@pytest.fixture(scope="function")
def engine():
    _engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in _SEED_TABLES:
        table.create(bind=_engine, checkfirst=True)
    yield _engine
    for table in reversed(_SEED_TABLES):
        table.drop(bind=_engine, checkfirst=True)


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


@pytest.fixture(scope="function")
def db_session(engine):
    """Yield a SQLAlchemy Session bound to the test engine.

    Each test gets a fresh in-memory DB (engine is function-scoped).
    No rollback/savepoint magic — the engine fixture drops tables at teardown.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
