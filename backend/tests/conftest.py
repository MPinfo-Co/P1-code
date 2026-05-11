import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")

# SQLite compatibility patches for in-memory testing.
# 1. JSONB → rendered as JSON (SQLite has no JSONB type).
# 2. BIGINT → rendered as INTEGER so SQLite autoincrement works correctly.
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler  # noqa: E402


def _visit_JSONB(self, type_, **kw):  # noqa: N802
    return self.visit_JSON(type_, **kw)


def _visit_BIGINT(self, type_, **kw):  # noqa: N802
    return "INTEGER"


SQLiteTypeCompiler.visit_JSONB = _visit_JSONB  # type: ignore[method-assign]
SQLiteTypeCompiler.visit_BIGINT = _visit_BIGINT  # type: ignore[method-assign]

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.connector import get_db
from app.main import app
from app.db.models.analysis import ChunkResult, DailyAnalysis, LogBatch
from app.db.models.events import EventHistory, SecurityEvent
from app.db.models.fn_ai_partner_chat import Conversation, Message, RoleAiPartner
from app.db.models.fn_ai_partner_config import AiPartnerConfig, AiPartnerTool
from app.db.models.fn_ai_partner_tool import Tool, ToolBodyParam
from app.db.models.fn_company_data import CompanyData
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
    # Event / pipeline tables (needed for /events/* endpoints)
    SecurityEvent.__table__,
    EventHistory.__table__,
    LogBatch.__table__,
    ChunkResult.__table__,
    DailyAnalysis.__table__,
    CompanyData.__table__,
    ExpertSetting.__table__,
]

# Pipeline / analysis tables — used by db_session fixture (haiku/pro/smoke tests)
_PIPELINE_TABLES = [
    User.__table__,
    SecurityEvent.__table__,
    EventHistory.__table__,
    LogBatch.__table__,
    ChunkResult.__table__,
    DailyAnalysis.__table__,
    CompanyData.__table__,
    ExpertSetting.__table__,
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
    """In-memory SQLite session for pipeline task tests (haiku/pro/smoke/company-data)."""
    _engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in _PIPELINE_TABLES:
        table.create(bind=_engine, checkfirst=True)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        for table in reversed(_PIPELINE_TABLES):
            table.drop(bind=_engine, checkfirst=True)
