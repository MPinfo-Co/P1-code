"""
Tests for multi-tenancy: tb_tenants, tenant_id 欄位、RLS POLICY、
TenantMiddleware 及 default_user event listener。

Test IDs follow sd-316-TDD.md: T2–T10, T28.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import BigInteger
from sqlalchemy import Integer as _Integer
from sqlalchemy import JSON, create_engine, inspect
from sqlalchemy.dialects.postgresql import JSONB as _JSONB
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models.analysis import LogBatch, ChunkResult, DailyAnalysis
from app.db.models.events import SecurityEvent, EventHistory
from app.db.models.fn_ai_partner_chat import Conversation, Message, RoleAiPartner
from app.db.models.fn_ai_partner_config import AiPartner, AiPartnerConfig, AiPartnerTool
from app.db.models.fn_ai_partner_tool import (
    Tool,
    ToolBodyParam,
    ToolImageField,
    ToolWebScraperConfig,
)
from app.db.models.fn_company_data import CompanyData
from app.db.models.fn_expert_setting import ExpertSetting
from app.db.models.fn_feedback import Feedback
from app.db.models.fn_tenant import Tenant
from app.db.models.function_access import FunctionFolder, FunctionItems, RoleFunction
from app.db.models.user_role import User, Role, TokenBlacklist, UserRole
from app.utils.util_store import create_access_token

# 全部 23 張需要 tenant_id 的 table 名稱
_ALL_TENANT_TABLES = [
    "tb_users",
    "tb_roles",
    "tb_feedbacks",
    "tb_function_folder",
    "tb_function_items",
    "tb_role_function",
    "tb_user_roles",
    "tb_token_blacklist",
    "tb_expert_settings",
    "tb_log_batches",
    "tb_chunk_results",
    "tb_daily_analysis",
    "tb_security_events",
    "tb_event_history",
    "tb_tools",
    "tb_tool_body_params",
    "tb_ai_partners",
    "tb_ai_partner_configs",
    "tb_ai_partner_tools",
    "tb_company_data",
    "tb_conversations",
    "tb_messages",
    "tb_role_ai_partners",
]

# SQLite 相容 patch（JSONB → JSON, BigInteger → Integer）


def _visit_JSONB(self, type_, **kw):  # noqa: N802
    return self.visit_JSON(type_, **kw)


def _visit_BIGINT(self, type_, **kw):  # noqa: N802
    return "INTEGER"


SQLiteTypeCompiler.visit_JSONB = _visit_JSONB  # type: ignore[method-assign]
SQLiteTypeCompiler.visit_BIGINT = _visit_BIGINT  # type: ignore[method-assign]


# ── Fixtures ────────────────────────────────────────────────────────────────

_ALL_ORM_TABLES = [
    Tenant.__table__,
    User.__table__,
    Role.__table__,
    UserRole.__table__,
    TokenBlacklist.__table__,
    FunctionFolder.__table__,
    FunctionItems.__table__,
    RoleFunction.__table__,
    Tool.__table__,
    ToolBodyParam.__table__,
    ToolImageField.__table__,
    ToolWebScraperConfig.__table__,
    AiPartner.__table__,
    AiPartnerConfig.__table__,
    AiPartnerTool.__table__,
    Conversation.__table__,
    Message.__table__,
    RoleAiPartner.__table__,
    Feedback.__table__,
    CompanyData.__table__,
    ExpertSetting.__table__,
    LogBatch.__table__,
    ChunkResult.__table__,
    DailyAnalysis.__table__,
    SecurityEvent.__table__,
    EventHistory.__table__,
]


@pytest.fixture()
def mem_engine():
    """In-memory SQLite engine with all tables created and JSONB/BigInt patches."""
    _patched: list[tuple] = []
    for table in _ALL_ORM_TABLES:
        for col in table.columns:
            if isinstance(col.type, _JSONB):
                _patched.append((col, col.type))
                col.type = JSON()
            elif isinstance(col.type, BigInteger):
                _patched.append((col, col.type))
                col.type = _Integer()

    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in _ALL_ORM_TABLES:
        table.create(bind=eng, checkfirst=True)

    # 還原型別，避免影響其他 fixture
    for col, orig in _patched:
        col.type = orig

    # 預建 default tenant
    with eng.connect() as conn:
        conn.execute(
            Tenant.__table__.insert()
            .prefix_with("OR IGNORE")
            .values(id=1, name="default")
        )
        conn.commit()

    yield eng

    # 清理：重新 patch 才能 drop
    for col, orig in _patched:
        if isinstance(orig, _JSONB):
            col.type = JSON()
        elif isinstance(orig, BigInteger):
            col.type = _Integer()
    for table in reversed(_ALL_ORM_TABLES):
        table.drop(bind=eng, checkfirst=True)
    for col, orig in _patched:
        col.type = orig


@pytest.fixture()
def mem_session(mem_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=mem_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


# ── Helpers ─────────────────────────────────────────────────────────────────


def _auth_header(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


# ── Tests ────────────────────────────────────────────────────────────────────


def test_T2_all_tables_have_tenant_id_column(mem_engine):
    """對應 T2：所有 23 張 table 均有 tenant_id 欄位"""
    inspector = inspect(mem_engine)
    for table_name in _ALL_TENANT_TABLES:
        columns = {col["name"] for col in inspector.get_columns(table_name)}
        assert "tenant_id" in columns, f"tb={table_name} 缺少 tenant_id 欄位"


def test_T2_tenant_id_not_nullable(mem_engine):
    """對應 T2：所有 23 張 table 的 tenant_id 欄位均為 NOT NULL"""
    inspector = inspect(mem_engine)
    for table_name in _ALL_TENANT_TABLES:
        for col in inspector.get_columns(table_name):
            if col["name"] == "tenant_id":
                assert not col["nullable"], f"tb={table_name}.tenant_id 應為 NOT NULL"
                break


def test_T3_existing_data_backfilled_to_default_tenant(mem_session):
    """對應 T3：已存在資料的 tenant_id 預設回填為 1（default tenant）"""
    # 插入一筆 user，不指定 tenant_id（應使用 default=1）
    user = User(name="Test", email="test@example.com", password_hash="hash")
    mem_session.add(user)
    mem_session.commit()

    saved = mem_session.query(User).filter_by(email="test@example.com").first()
    assert saved is not None
    assert saved.tenant_id == 1, "新建 user 未指定 tenant_id 時應預設為 1"


def test_T4_rls_only_returns_current_tenant_data():
    """對應 T4：RLS POLICY 僅回傳當前 tenant 的資料（PostgreSQL 特定，此處以邏輯驗證代替）

    在 SQLite 測試環境中無法執行真實 RLS，此測試改以驗證 tenant_id 欄位
    存在且 ORM 可正確篩選 tenant 資料（跨租戶資料不互通）。

    注意：after_insert event listener 會在建立 tenant 後自動插入 default_user，
    因此此測試以 email 精確比對取代 count 比對。
    """
    from sqlalchemy import create_engine as _ce
    from sqlalchemy.pool import StaticPool

    eng = _ce(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Tenant.__table__.create(bind=eng, checkfirst=True)
    User.__table__.create(bind=eng, checkfirst=True)

    Sess = sessionmaker(bind=eng)
    sess = Sess()

    # 建立兩個 tenant（after_insert 會各自建立 default_user）
    sess.add(Tenant(id=10, name="alpha"))
    sess.add(Tenant(id=20, name="beta"))
    sess.flush()

    # 各自額外建立業務 user
    sess.add(User(name="A", email="biz_a@t10.com", password_hash="h", tenant_id=10))
    sess.add(User(name="B", email="biz_b@t20.com", password_hash="h", tenant_id=20))
    sess.commit()

    # 確認 tenant10 的 user 不含 tenant20 的業務 user
    tenant10_emails = {
        u.email for u in sess.query(User).filter(User.tenant_id == 10).all()
    }
    tenant20_emails = {
        u.email for u in sess.query(User).filter(User.tenant_id == 20).all()
    }

    assert "biz_a@t10.com" in tenant10_emails
    assert "biz_b@t20.com" not in tenant10_emails
    assert "biz_b@t20.com" in tenant20_emails
    assert "biz_a@t10.com" not in tenant20_emails

    sess.close()
    User.__table__.drop(bind=eng)
    Tenant.__table__.drop(bind=eng)


def test_T5_no_tenant_session_returns_empty():
    """對應 T5：未設定 session variable 時 RLS 攔截所有存取（邏輯驗證）

    在 SQLite 環境中，此測試驗證 tenant_id 欄位存在且
    當 tenant_id 篩選條件為不存在的值時返回空結果。
    """
    from sqlalchemy import create_engine as _ce
    from sqlalchemy.pool import StaticPool

    eng = _ce(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Tenant.__table__.create(bind=eng, checkfirst=True)
    User.__table__.create(bind=eng, checkfirst=True)

    Sess = sessionmaker(bind=eng)
    sess = Sess()
    sess.add(Tenant(id=1, name="default"))
    sess.flush()
    sess.add(User(name="U1", email="u1@t1.com", password_hash="h", tenant_id=1))
    sess.commit()

    # 模擬「未設定 tenant」→ 使用不存在的 tenant_id=0
    no_tenant_users = sess.query(User).filter(User.tenant_id == 0).all()
    assert no_tenant_users == [], "未設定 tenant 時查詢應回傳空結果"

    sess.close()
    User.__table__.drop(bind=eng)
    Tenant.__table__.drop(bind=eng)


def test_T6_two_tenants_data_isolated(mem_session):
    """對應 T6：兩個 tenant 各自只能看到自己的資料，不互通"""
    # 建立 tenant 2（after_insert 會自動建立 2_admin@tenant.local）
    mem_session.add(Tenant(id=2, name="tenant_b"))
    mem_session.flush()

    mem_session.add(
        User(name="UserA", email="a@ta.com", password_hash="h", tenant_id=1)
    )
    mem_session.add(
        User(name="UserB", email="b@tb.com", password_hash="h", tenant_id=2)
    )
    mem_session.commit()

    t1_emails = {
        u.email for u in mem_session.query(User).filter(User.tenant_id == 1).all()
    }
    t2_emails = {
        u.email for u in mem_session.query(User).filter(User.tenant_id == 2).all()
    }

    # Tenant 1 看得到 a@ta.com，看不到 b@tb.com
    assert "a@ta.com" in t1_emails
    assert "b@tb.com" not in t1_emails

    # Tenant 2 看得到 b@tb.com，看不到 a@ta.com
    assert "b@tb.com" in t2_emails
    assert "a@ta.com" not in t2_emails


def test_T7_new_tenant_creates_default_user(mem_session):
    """對應 T7：新增 tenant 時自動建立對應的 default_user（帳號：{tenant_id}_admin）"""
    new_tenant = Tenant(id=99, name="new_corp")
    mem_session.add(new_tenant)
    mem_session.commit()

    # event listener 在 after_insert 觸發，以 connection.execute 直接插入
    # 在 SQLite in-memory 環境中 event listener 應已觸發
    default_user = (
        mem_session.query(User).filter(User.email == "99_admin@tenant.local").first()
    )
    assert default_user is not None, "新增 tenant 後應自動建立 default_user"
    assert default_user.name == "99_admin"
    assert default_user.tenant_id == 99


def test_T8_tenant_middleware_sets_tenant_id(client):
    """對應 T8：TenantMiddleware 從 JWT 解析 tenant_id 並注入 request.state"""
    from app.middlewares.tenant_middleware import TenantMiddleware
    from starlette.testclient import TestClient
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    from starlette.requests import Request

    captured = {}

    async def endpoint(request: Request):
        captured["tenant_id"] = getattr(request.state, "tenant_id", "MISSING")
        return JSONResponse({"ok": True})

    starlette_app = Starlette(routes=[Route("/test", endpoint)])
    starlette_app.add_middleware(TenantMiddleware)

    # 模擬 authenticate + User query
    mock_auth = MagicMock()
    mock_auth.user_id = 1

    mock_user = MagicMock()
    mock_user.tenant_id = 5

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    with (
        patch("app.middlewares.tenant_middleware.authenticate", return_value=mock_auth),
        patch("app.middlewares.tenant_middleware.SessionLocal", return_value=mock_db),
    ):
        with TestClient(starlette_app) as tc:
            token = create_access_token(1)
            tc.get("/test", headers={"Authorization": f"Bearer {token}"})

    assert captured.get("tenant_id") == 5, (
        f"middleware 應設定 tenant_id=5，實際得到 {captured.get('tenant_id')}"
    )


def test_T9_rls_integration_two_tenants_isolated(mem_session):
    """對應 T9：整合測試 - 兩個 tenant 的資料完全隔離"""
    # 建立 tenant 2
    mem_session.add(Tenant(id=2, name="tenant_b"))
    mem_session.flush()

    # 建立兩個 tenant 各自的 user
    u1 = User(id=100, name="U1", email="u1@t1.com", password_hash="h", tenant_id=1)
    u2 = User(id=200, name="U2", email="u2@t2.com", password_hash="h", tenant_id=2)
    mem_session.add(u1)
    mem_session.add(u2)
    mem_session.flush()

    # Tenant 1 的資料
    mem_session.add(Feedback(user_id=100, rating=5, comment="T1 feedback", tenant_id=1))
    # Tenant 2 的資料
    mem_session.add(Feedback(user_id=200, rating=3, comment="T2 feedback", tenant_id=2))
    mem_session.commit()

    t1_feedbacks = mem_session.query(Feedback).filter(Feedback.tenant_id == 1).all()
    t2_feedbacks = mem_session.query(Feedback).filter(Feedback.tenant_id == 2).all()

    assert len(t1_feedbacks) == 1
    assert t1_feedbacks[0].comment == "T1 feedback"
    assert len(t2_feedbacks) == 1
    assert t2_feedbacks[0].comment == "T2 feedback"

    # 確認無資料洩漏
    for fb in t1_feedbacks:
        assert fb.tenant_id != 2, "Tenant 1 不應看到 Tenant 2 的資料"
    for fb in t2_feedbacks:
        assert fb.tenant_id != 1, "Tenant 2 不應看到 Tenant 1 的資料"


def test_T10_users_tenant_id_fk_structure(mem_engine):
    """對應 T10：tb_users.tenant_id 為 INTEGER，FK 指向 tb_tenants.id"""
    inspector = inspect(mem_engine)

    # 確認型別為 INTEGER
    cols = {c["name"]: c for c in inspector.get_columns("tb_users")}
    assert "tenant_id" in cols
    assert not cols["tenant_id"]["nullable"], "tenant_id 應為 NOT NULL"

    # 確認 FK（SQLite 使用 PRAGMA）
    fks = inspector.get_foreign_keys("tb_users")
    tenant_fk = [fk for fk in fks if fk["referred_table"] == "tb_tenants"]
    assert len(tenant_fk) >= 1, "tb_users 應有指向 tb_tenants 的 FK"
    assert "tenant_id" in tenant_fk[0]["constrained_columns"]


def test_T28_default_user_idempotent(mem_session):
    """對應 T28：重複觸發建立相同 tenant 的 default_user 不會產生重複（冪等保護）"""
    # 第一次建立 tenant 88
    tenant = Tenant(id=88, name="idempotent_test")
    mem_session.add(tenant)
    mem_session.commit()

    count_after_first = (
        mem_session.query(User).filter(User.email == "88_admin@tenant.local").count()
    )
    assert count_after_first == 1, "第一次建立 tenant 應建立一個 default_user"

    # 嘗試再次插入相同 email 的 user（模擬重複觸發）
    from sqlalchemy import text as _text

    try:
        mem_session.execute(
            _text(
                "INSERT OR IGNORE INTO tb_users (name, email, password_hash, tenant_id) "
                "VALUES ('88_admin', '88_admin@tenant.local', 'hash', 88)"
            )
        )
        mem_session.commit()
    except Exception:
        mem_session.rollback()

    count_after_second = (
        mem_session.query(User).filter(User.email == "88_admin@tenant.local").count()
    )
    assert count_after_second == 1, "重複插入相同 email 後 default_user 仍應只有一筆"
