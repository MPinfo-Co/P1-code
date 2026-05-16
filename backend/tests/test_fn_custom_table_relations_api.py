"""
Tests for fn_custom_table_relations APIs:
  GET  /custom_table/relations
  PUT  /custom_table/relations

對應測試案例 T28–T37
"""

import os

from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_custom_table import (
    CustomTable,
    CustomTableField,
    CustomTableRelation,
)
from app.db.models.function_access import (
    FunctionItems as Function,
    FunctionFolder,
    RoleFunction,
)
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password

os.environ.setdefault("AES_KEY", "test-aes-256-key-for-pytest-12345")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_folder(db: Session, name: str = "自訂資料表", sort_order: int = 1) -> int:
    folder = FunctionFolder(folder_code=name, folder_label=name, sort_order=sort_order)
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db: Session, name: str, folder_id: int, sort_order: int = 1) -> int:
    fn = Function(
        function_code=name,
        function_label=name,
        folder_id=folder_id,
        sort_order=sort_order,
    )
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db: Session, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(db: Session, email: str, name: str = "Test User") -> int:
    user = User(name=name, email=email, password_hash=hash_password("password123"))
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _grant_function(db: Session, role_id: int, function_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=function_id))
    db.flush()


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_admin_with_fn_custom_table(engine, suffix: str = "") -> tuple[int, int, int]:
    """Create user + role + fn_custom_table permission. Return (user_id, role_id, fn_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db, f"自訂資料表{suffix}", 1)
    fn_id = _make_function(db, "fn_custom_table", folder_id, 5)
    role_id = _make_role(db, f"admin_ct_rel{suffix}")
    user_id = _make_user(
        db, f"admin_ct_rel{suffix}@test.com", name=f"Admin CT Rel{suffix}"
    )
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_id


def _setup_no_perm_user(engine, suffix: str = "") -> int:
    """Create user without fn_custom_table permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, f"no_perm_rel{suffix}")
    user_id = _make_user(db, f"no_perm_rel{suffix}@test.com")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id


def _create_table(engine, name: str) -> int:
    """Insert a custom table with one field. Return table id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    table = CustomTable(name=name, description="test")
    db.add(table)
    db.flush()
    db.add(
        CustomTableField(
            table_id=table.id,
            field_name="欄位A",
            field_type="string",
            sort_order=0,
        )
    )
    db.commit()
    tid = table.id
    db.close()
    return tid


def _create_relation(
    engine, src_table_id: int, src_field: str, dst_table_id: int, dst_field: str
) -> int:
    """Insert a relation row. Return id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    rel = CustomTableRelation(
        src_table_id=src_table_id,
        src_field=src_field,
        dst_table_id=dst_table_id,
        dst_field=dst_field,
    )
    db.add(rel)
    db.commit()
    rid = rel.id
    db.close()
    return rid


# ---------------------------------------------------------------------------
# T28: GET /custom_table/relations — 有資料（2 筆）
# ---------------------------------------------------------------------------


def test_list_relations_returns_data(client, engine):
    """對應 T28"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine, "_t28")
    tbl1 = _create_table(engine, "來源表T28")
    tbl2 = _create_table(engine, "目標表T28")
    _create_relation(engine, tbl1, "客戶ID", tbl2, "id")
    _create_relation(engine, tbl2, "id", tbl1, "客戶ID")

    resp = client.get("/custom_table/relations", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    relations = body["data"]["relations"]
    assert len(relations) == 2
    # 確認欄位存在
    for r in relations:
        assert "id" in r
        assert "src_table_id" in r
        assert "src_field" in r
        assert "dst_table_id" in r
        assert "dst_field" in r


# ---------------------------------------------------------------------------
# T29: GET /custom_table/relations — 空資料
# ---------------------------------------------------------------------------


def test_list_relations_empty(client, engine):
    """對應 T29"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine, "_t29")

    resp = client.get("/custom_table/relations", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert body["data"]["relations"] == []


# ---------------------------------------------------------------------------
# T30: GET /custom_table/relations — 無權限
# ---------------------------------------------------------------------------


def test_list_relations_no_permission(client, engine):
    """對應 T30"""
    user_id = _setup_no_perm_user(engine, "_t30")

    resp = client.get("/custom_table/relations", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# T31: PUT /custom_table/relations — 覆寫成功（3 筆覆寫舊 2 筆）
# ---------------------------------------------------------------------------


def test_save_relations_overwrite(client, engine):
    """對應 T31"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine, "_t31")
    tbl1 = _create_table(engine, "表一T31")
    tbl2 = _create_table(engine, "表二T31")
    tbl3 = _create_table(engine, "表三T31")

    # 先建立 2 筆舊關聯
    _create_relation(engine, tbl1, "欄A", tbl2, "欄B")
    _create_relation(engine, tbl2, "欄B", tbl1, "欄A")

    # 送入 3 筆新關聯
    payload = {
        "relations": [
            {
                "src_table_id": tbl1,
                "src_field": "欄X",
                "dst_table_id": tbl2,
                "dst_field": "欄Y",
            },
            {
                "src_table_id": tbl2,
                "src_field": "欄Y",
                "dst_table_id": tbl3,
                "dst_field": "欄Z",
            },
            {
                "src_table_id": tbl3,
                "src_field": "欄Z",
                "dst_table_id": tbl1,
                "dst_field": "欄X",
            },
        ]
    }
    resp = client.put(
        "/custom_table/relations", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "儲存成功"

    # 確認 DB 只有 3 筆
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    count = db.query(CustomTableRelation).count()
    db.close()
    assert count == 3


# ---------------------------------------------------------------------------
# T32: PUT /custom_table/relations — 傳空陣列，清除全部
# ---------------------------------------------------------------------------


def test_save_relations_clear_all(client, engine):
    """對應 T32"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine, "_t32")
    tbl1 = _create_table(engine, "表一T32")
    tbl2 = _create_table(engine, "表二T32")
    _create_relation(engine, tbl1, "欄A", tbl2, "欄B")

    payload = {"relations": []}
    resp = client.put(
        "/custom_table/relations", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "儲存成功"

    # 確認 DB 關聯全被清除
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    count = db.query(CustomTableRelation).count()
    db.close()
    assert count == 0


# ---------------------------------------------------------------------------
# T33: PUT /custom_table/relations — 自我關聯失敗
# ---------------------------------------------------------------------------


def test_save_relations_self_relation_fails(client, engine):
    """對應 T33"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine, "_t33")
    tbl1 = _create_table(engine, "表一T33")

    payload = {
        "relations": [
            {
                "src_table_id": tbl1,
                "src_field": "欄A",
                "dst_table_id": tbl1,
                "dst_field": "欄A",
            },
        ]
    }
    resp = client.put(
        "/custom_table/relations", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "不允許自我關聯（來源與目標為同一表格的同一欄位）"


# ---------------------------------------------------------------------------
# T34: PUT /custom_table/relations — 重複關聯失敗
# ---------------------------------------------------------------------------


def test_save_relations_duplicate_fails(client, engine):
    """對應 T34"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine, "_t34")
    tbl1 = _create_table(engine, "表一T34")
    tbl2 = _create_table(engine, "表二T34")

    payload = {
        "relations": [
            {
                "src_table_id": tbl1,
                "src_field": "欄A",
                "dst_table_id": tbl2,
                "dst_field": "欄B",
            },
            {
                "src_table_id": tbl1,
                "src_field": "欄A",
                "dst_table_id": tbl2,
                "dst_field": "欄B",
            },
        ]
    }
    resp = client.put(
        "/custom_table/relations", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "不允許重複的關聯組合"


# ---------------------------------------------------------------------------
# T35: PUT /custom_table/relations — 來源資料表不存在
# ---------------------------------------------------------------------------


def test_save_relations_src_table_not_found(client, engine):
    """對應 T35"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine, "_t35")
    tbl2 = _create_table(engine, "目標表T35")

    payload = {
        "relations": [
            {
                "src_table_id": 99999,
                "src_field": "欄A",
                "dst_table_id": tbl2,
                "dst_field": "欄B",
            },
        ]
    }
    resp = client.put(
        "/custom_table/relations", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "來源資料表不存在"


# ---------------------------------------------------------------------------
# T36: PUT /custom_table/relations — 目標資料表不存在
# ---------------------------------------------------------------------------


def test_save_relations_dst_table_not_found(client, engine):
    """對應 T36"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine, "_t36")
    tbl1 = _create_table(engine, "來源表T36")

    payload = {
        "relations": [
            {
                "src_table_id": tbl1,
                "src_field": "欄A",
                "dst_table_id": 99999,
                "dst_field": "欄B",
            },
        ]
    }
    resp = client.put(
        "/custom_table/relations", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "目標資料表不存在"


# ---------------------------------------------------------------------------
# T37: PUT /custom_table/relations — 無權限
# ---------------------------------------------------------------------------


def test_save_relations_no_permission(client, engine):
    """對應 T37"""
    user_id = _setup_no_perm_user(engine, "_t37")
    # 需要一個合法 table 存在（但不影響權限驗證順序）

    payload = {
        "relations": [
            {
                "src_table_id": 1,
                "src_field": "欄A",
                "dst_table_id": 2,
                "dst_field": "欄B",
            },
        ]
    }
    resp = client.put(
        "/custom_table/relations", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"
