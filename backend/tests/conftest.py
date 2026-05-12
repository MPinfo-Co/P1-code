import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.connector import get_db
from app.main import app
from app.db.models.analysis import ChunkResult, DailyAnalysis, LogBatch
from app.db.models.events import SecurityEvent
from app.db.models.fn_ai_partner_chat import Conversation, Message, RoleAiPartner
from app.db.models.fn_ai_partner_config import AiPartnerConfig, AiPartnerTool
from app.db.models.fn_ai_partner_tool import Tool, ToolBodyParam
from app.db.models.fn_expert_setting import ExpertSetting
from app.db.models.fn_feedback import Feedback
from app.db.models.function_access import (
    FunctionItems as Function,
    FunctionFolder,
    RoleFunction,
)
from app.db.models.user_role import Role, TokenBlacklist, User, UserRole

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
    AiPartnerConfig.__table__,
    AiPartnerTool.__table__,
    Conversation.__table__,
    Message.__table__,
    RoleAiPartner.__table__,
    Feedback.__table__,
]

_TASK_TABLES = [
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
def db_session():
    """In-memory SQLAlchemy session for unit tests that need direct DB access.

    Creates all task-related tables (LogBatch, ChunkResult, etc.) alongside
    the common seed tables so scheduler / task tests can exercise DB I/O.

    Two compatibility patches are applied temporarily for SQLite:
    - JSONB columns → JSON  (SQLite has no native JSONB)
    - BigInteger PK columns → Integer  (SQLite RETURNING does not support BIGINT autoincrement)
    """
    from sqlalchemy import BigInteger, Integer, JSON
    from sqlalchemy.dialects.postgresql import JSONB as _JSONB

    all_tables = _SEED_TABLES + _TASK_TABLES

    _patched: list[tuple] = []
    for table in all_tables:
        for col in table.columns:
            if isinstance(col.type, _JSONB):
                _patched.append((col, col.type))
                col.type = JSON()
            elif isinstance(col.type, BigInteger):
                _patched.append((col, col.type))
                col.type = Integer()

    _engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in all_tables:
        table.create(bind=_engine, checkfirst=True)

    # Restore original types so other tests / the real app are not affected
    for col, original_type in _patched:
        col.type = original_type

    Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        # Re-patch to allow drop
        for col, original_type in _patched:
            orig = original_type
            if isinstance(orig, _JSONB):
                col.type = JSON()
            elif isinstance(orig, BigInteger):
                col.type = Integer()
        for table in reversed(all_tables):
            table.drop(bind=_engine, checkfirst=True)
        for col, original_type in _patched:
            col.type = original_type
