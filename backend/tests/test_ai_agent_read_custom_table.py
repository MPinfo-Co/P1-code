"""
Tests for ai_agent._execute_read_custom_table 結構化查詢功能
對應 TDD #4 測試案例 T1–T17
"""

import json
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")

from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy import BigInteger, Integer, JSON
from sqlalchemy.dialects.postgresql import JSONB as _JSONB

from app.db.models.fn_custom_table import (
    CustomTable,
    CustomTableField,
    CustomTableRecord,
)
from app.db.models.user_role import User
from app.utils.util_store import hash_password
from app.services.ai_agent import _execute_read_custom_table


# ---------------------------------------------------------------------------
# SQLite 相容性 patch（JSONB → JSON, BigInteger → Integer）
# ---------------------------------------------------------------------------


def _visit_JSONB(self, type_, **kw):  # noqa: N802
    return self.visit_JSON(type_, **kw)


def _visit_BIGINT(self, type_, **kw):  # noqa: N802
    return "INTEGER"


SQLiteTypeCompiler.visit_JSONB = _visit_JSONB  # type: ignore[method-assign]
SQLiteTypeCompiler.visit_BIGINT = _visit_BIGINT  # type: ignore[method-assign]

_TABLES = [
    User.__table__,
    CustomTable.__table__,
    CustomTableField.__table__,
    CustomTableRecord.__table__,
]

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture()
def db_session():
    """建立 SQLite in-memory session，並 patch JSONB/BigInteger 型別。"""
    _patched: list[tuple] = []
    for table in _TABLES:
        for col in table.columns:
            if isinstance(col.type, _JSONB):
                _patched.append((col, col.type))
                col.type = JSON()
            elif isinstance(col.type, BigInteger):
                _patched.append((col, col.type))
                col.type = Integer()

    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in _TABLES:
        table.create(bind=engine, checkfirst=True)

    # 還原原始型別（避免影響其他測試）
    for col, original_type in _patched:
        col.type = original_type

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        for col, original_type in _patched:
            if isinstance(original_type, _JSONB):
                col.type = JSON()
            elif isinstance(original_type, BigInteger):
                col.type = Integer()
        for table in reversed(_TABLES):
            table.drop(bind=engine, checkfirst=True)
        for col, original_type in _patched:
            col.type = original_type


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _make_user(db, email: str = "user@test.com") -> int:
    u = User(name="Test User", email=email, password_hash=hash_password("pw"))
    db.add(u)
    db.flush()
    return u.id


def _make_table(db) -> int:
    t = CustomTable(name="測試資料表", description="test")
    db.add(t)
    db.flush()
    return t.id


def _make_record(db, table_id: int, user_id: int, data: dict) -> int:
    r = CustomTableRecord(table_id=table_id, data=data, updated_by=user_id)
    db.add(r)
    db.flush()
    return r.id


def _config(table_id: int, user_id: int, scope: str = "all", limit: int = 20) -> dict:
    return {
        "name": "read_custom_table",
        "tool_type": "read_custom_table",
        "target_table_id": table_id,
        "limit": limit,
        "scope": scope,
        "user_id": user_id,
    }


# ---------------------------------------------------------------------------
# T1：無參數退化為原行為
# ---------------------------------------------------------------------------


def test_no_params_returns_default_behavior(db_session):
    """對應 T1"""
    user_id = _make_user(db_session, "t1@test.com")
    table_id = _make_table(db_session)
    for i in range(5):
        _make_record(db_session, table_id, user_id, {"idx": i})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    result_str = _execute_read_custom_table(config, {}, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 5


# ---------------------------------------------------------------------------
# T2：eq 過濾
# ---------------------------------------------------------------------------


def test_eq_filter_returns_matching_records(db_session):
    """對應 T2"""
    user_id = _make_user(db_session, "t2@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"status": "active"})
    _make_record(db_session, table_id, user_id, {"status": "inactive"})
    _make_record(db_session, table_id, user_id, {"status": "active"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"filters": [{"field": "status", "op": "eq", "value": "active"}]}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 2
    for r in result:
        assert r["status"] == "active"


# ---------------------------------------------------------------------------
# T3：gt 過濾
# ---------------------------------------------------------------------------


def test_gt_filter_returns_matching_records(db_session):
    """對應 T3"""
    user_id = _make_user(db_session, "t3@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"amount": "50"})
    _make_record(db_session, table_id, user_id, {"amount": "100"})
    _make_record(db_session, table_id, user_id, {"amount": "150"})
    _make_record(db_session, table_id, user_id, {"amount": "200"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"filters": [{"field": "amount", "op": "gt", "value": 100}]}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 2
    amounts = [float(r["amount"]) for r in result]
    for a in amounts:
        assert a > 100


# ---------------------------------------------------------------------------
# T4：contains 過濾
# ---------------------------------------------------------------------------


def test_contains_filter_returns_matching_records(db_session):
    """對應 T4"""
    user_id = _make_user(db_session, "t4@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"name": "王小明"})
    _make_record(db_session, table_id, user_id, {"name": "李大華"})
    _make_record(db_session, table_id, user_id, {"name": "王建國"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"filters": [{"field": "name", "op": "contains", "value": "王"}]}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 2
    for r in result:
        assert "王" in r["name"]


# ---------------------------------------------------------------------------
# T5：AND 條件組合
# ---------------------------------------------------------------------------


def test_and_condition_returns_matching_records(db_session):
    """對應 T5"""
    user_id = _make_user(db_session, "t5@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"status": "active", "level": "3"})
    _make_record(db_session, table_id, user_id, {"status": "active", "level": "1"})
    _make_record(db_session, table_id, user_id, {"status": "inactive", "level": "3"})
    _make_record(db_session, table_id, user_id, {"status": "active", "level": "2"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {
        "filters": [
            {
                "logic": "AND",
                "conditions": [
                    {"field": "status", "op": "eq", "value": "active"},
                    {"field": "level", "op": "gte", "value": 2},
                ],
            }
        ]
    }
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 2
    for r in result:
        assert r["status"] == "active"
        assert int(r["level"]) >= 2


# ---------------------------------------------------------------------------
# T6：OR 條件組合
# ---------------------------------------------------------------------------


def test_or_condition_returns_matching_records(db_session):
    """對應 T6"""
    user_id = _make_user(db_session, "t6@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"category": "A"})
    _make_record(db_session, table_id, user_id, {"category": "B"})
    _make_record(db_session, table_id, user_id, {"category": "C"})
    _make_record(db_session, table_id, user_id, {"category": "A"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {
        "filters": [
            {
                "logic": "OR",
                "conditions": [
                    {"field": "category", "op": "eq", "value": "A"},
                    {"field": "category", "op": "eq", "value": "B"},
                ],
            }
        ]
    }
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 3
    for r in result:
        assert r["category"] in ("A", "B")


# ---------------------------------------------------------------------------
# T7：自訂排序
# ---------------------------------------------------------------------------


def test_custom_sort_returns_ordered_records(db_session):
    """對應 T7"""
    user_id = _make_user(db_session, "t7@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"score": "30"})
    _make_record(db_session, table_id, user_id, {"score": "10"})
    _make_record(db_session, table_id, user_id, {"score": "20"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"sort": {"field": "score", "direction": "asc"}}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 3
    scores = [r["score"] for r in result]
    # 字串排序：'10' < '20' < '30'（SQLite JSON 提取為字串）
    assert scores == sorted(scores)


# ---------------------------------------------------------------------------
# T8：count 聚合
# ---------------------------------------------------------------------------


def test_count_aggregate_returns_count(db_session):
    """對應 T8"""
    user_id = _make_user(db_session, "t8@test.com")
    table_id = _make_table(db_session)
    for i in range(7):
        _make_record(db_session, table_id, user_id, {"val": i})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"aggregate": {"func": "count"}}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, dict)
    assert "count" in result
    assert result["count"] == 7


# ---------------------------------------------------------------------------
# T9：sum 聚合
# ---------------------------------------------------------------------------


def test_sum_aggregate_returns_total(db_session):
    """對應 T9"""
    user_id = _make_user(db_session, "t9@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"amount": "100"})
    _make_record(db_session, table_id, user_id, {"amount": "200"})
    _make_record(db_session, table_id, user_id, {"amount": "300"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"aggregate": {"func": "sum", "field": "amount"}}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, dict)
    assert "sum" in result
    assert float(result["sum"]) == 600.0


# ---------------------------------------------------------------------------
# T10：avg 聚合
# ---------------------------------------------------------------------------


def test_avg_aggregate_returns_average(db_session):
    """對應 T10"""
    user_id = _make_user(db_session, "t10@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"amount": "100"})
    _make_record(db_session, table_id, user_id, {"amount": "200"})
    _make_record(db_session, table_id, user_id, {"amount": "300"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"aggregate": {"func": "avg", "field": "amount"}}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, dict)
    assert "avg" in result
    assert float(result["avg"]) == 200.0


# ---------------------------------------------------------------------------
# T11：group_by + sum 聚合
# ---------------------------------------------------------------------------


def test_group_by_sum_aggregate_returns_grouped_results(db_session):
    """對應 T11"""
    user_id = _make_user(db_session, "t11@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"category": "A", "amount": "100"})
    _make_record(db_session, table_id, user_id, {"category": "A", "amount": "50"})
    _make_record(db_session, table_id, user_id, {"category": "B", "amount": "200"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {
        "aggregate": {"func": "sum", "field": "amount", "group_by": "category"}
    }
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 2

    group_map = {r["category"]: r["sum"] for r in result}
    assert float(group_map["A"]) == 150.0
    assert float(group_map["B"]) == 200.0


# ---------------------------------------------------------------------------
# T12：scope='self' 過濾
# ---------------------------------------------------------------------------


def test_scope_self_filters_by_user(db_session):
    """對應 T12"""
    user1_id = _make_user(db_session, "t12user1@test.com")
    user2_id = _make_user(db_session, "t12user2@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user1_id, {"owner": "user1"})
    _make_record(db_session, table_id, user1_id, {"owner": "user1_2"})
    _make_record(db_session, table_id, user2_id, {"owner": "user2"})
    db_session.commit()

    config = _config(table_id, user1_id, scope="self")
    result_str = _execute_read_custom_table(config, {}, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 2
    for r in result:
        assert "user1" in r["owner"]


# ---------------------------------------------------------------------------
# T13：scope='all' 不過濾使用者
# ---------------------------------------------------------------------------


def test_scope_all_returns_all_users_records(db_session):
    """對應 T13"""
    user1_id = _make_user(db_session, "t13user1@test.com")
    user2_id = _make_user(db_session, "t13user2@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user1_id, {"owner": "user1"})
    _make_record(db_session, table_id, user2_id, {"owner": "user2"})
    db_session.commit()

    config = _config(table_id, user1_id, scope="all")
    result_str = _execute_read_custom_table(config, {}, db_session)
    result = json.loads(result_str)

    assert isinstance(result, list)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# T14：不存在欄位 → 空陣列，不 raise exception
# ---------------------------------------------------------------------------


def test_nonexistent_field_filter_returns_empty_list(db_session):
    """對應 T14"""
    user_id = _make_user(db_session, "t14@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"status": "active"})
    _make_record(db_session, table_id, user_id, {"status": "inactive"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"filters": [{"field": "nonexistent_field", "op": "eq", "value": "x"}]}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    # 不存在的欄位 JSONB 取值為 null，比較結果 false → 空陣列
    assert isinstance(result, list)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# T15：aggregate sum 未傳 field → 回傳錯誤訊息，agentic loop 繼續
# ---------------------------------------------------------------------------


def test_aggregate_sum_missing_field_returns_error_message(db_session):
    """對應 T15"""
    user_id = _make_user(db_session, "t15@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"amount": "100"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    # 僅傳 func，未傳 field
    tool_input = {"aggregate": {"func": "sum"}}
    result_str = _execute_read_custom_table(config, tool_input, db_session)

    # 應回傳錯誤訊息字串，不 raise exception
    assert "sum" in result_str
    assert "field" in result_str
    # 確認不是 JSON 陣列（不是正常資料）
    try:
        parsed = json.loads(result_str)
        # 若能解析，應為包含錯誤的 dict，不為 list
        assert not isinstance(parsed, list)
    except json.JSONDecodeError:
        # 純文字錯誤訊息亦可接受
        pass


# ---------------------------------------------------------------------------
# T16：min 聚合
# ---------------------------------------------------------------------------


def test_min_aggregate_returns_minimum(db_session):
    """對應 T16"""
    user_id = _make_user(db_session, "t16@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"amount": "500"})
    _make_record(db_session, table_id, user_id, {"amount": "100"})
    _make_record(db_session, table_id, user_id, {"amount": "300"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"aggregate": {"func": "min", "field": "amount"}}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, dict)
    assert "min" in result
    assert float(result["min"]) == 100.0


# ---------------------------------------------------------------------------
# T17：max 聚合
# ---------------------------------------------------------------------------


def test_max_aggregate_returns_maximum(db_session):
    """對應 T17"""
    user_id = _make_user(db_session, "t17@test.com")
    table_id = _make_table(db_session)
    _make_record(db_session, table_id, user_id, {"amount": "500"})
    _make_record(db_session, table_id, user_id, {"amount": "100"})
    _make_record(db_session, table_id, user_id, {"amount": "300"})
    db_session.commit()

    config = _config(table_id, user_id, scope="all")
    tool_input = {"aggregate": {"func": "max", "field": "amount"}}
    result_str = _execute_read_custom_table(config, tool_input, db_session)
    result = json.loads(result_str)

    assert isinstance(result, dict)
    assert "max" in result
    assert float(result["max"]) == 500.0
