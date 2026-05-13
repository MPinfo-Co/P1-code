"""
Tests for fn_custom_table APIs:
  GET    /custom_table
  POST   /custom_table
  PATCH  /custom_table/{id}
  DELETE /custom_table/{id}
  GET    /custom_table/options
"""

from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_ai_partner_tool import Tool
from app.db.models.fn_custom_table import (
    CustomTable,
    CustomTableField,
    CustomTableRecord,
)
from app.db.models.function_access import (
    FunctionItems as Function,
    FunctionFolder,
    RoleFunction,
)
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_function_folder(db: Session, name: str = "設定", sort_order: int = 2) -> int:
    folder = FunctionFolder(folder_code=name, folder_label=name, sort_order=sort_order)
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(
    db: Session, code: str, label: str, folder_id: int, sort_order: int = 1
) -> int:
    fn = Function(
        function_code=code,
        function_label=label,
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


def _setup_admin_with_fn_custom_table(engine):
    """Create admin user with fn_custom_table permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_function_folder(db, "設定", 2)
    fn_id = _make_function(db, "fn_custom_table", "自訂資料表", folder_id, 4)
    role_id = _make_role(db, "admin_ct")
    user_id = _make_user(db, "admin_ct@test.com", "Admin CT")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_id


def _setup_plain_user(engine, email: str = "plain_ct@test.com"):
    """Create user without fn_custom_table permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, f"plain_{email[:5]}")
    user_id = _make_user(db, email, "Plain CT User")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id


def _insert_custom_table(engine, name: str, fields: list[dict] | None = None) -> int:
    """Insert a custom table with optional fields. Return table id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    table = CustomTable(name=name, description=f"{name} 說明")
    db.add(table)
    db.flush()
    for idx, f in enumerate(
        fields or [{"field_name": "欄位A", "field_type": "string"}]
    ):
        db.add(
            CustomTableField(
                table_id=table.id,
                field_name=f["field_name"],
                field_type=f["field_type"],
                sort_order=idx,
            )
        )
    db.commit()
    tid = table.id
    db.close()
    return tid


def _insert_record(engine, table_id: int, data: dict | None = None) -> None:
    """Insert a record into a custom table."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    db.add(CustomTableRecord(table_id=table_id, data=data or {"欄位A": "值"}))
    db.commit()
    db.close()


def _insert_record_id(engine, table_id: int, data: dict | None = None) -> int:
    """Insert a record into a custom table and return its id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    record = CustomTableRecord(table_id=table_id, data=data or {"欄位A": "值"})
    db.add(record)
    db.flush()
    rid = record.id
    db.commit()
    db.close()
    return rid


# ---------------------------------------------------------------------------
# GET /custom_table — T1, T2, T3
# ---------------------------------------------------------------------------


def test_list_custom_tables_returns_200(client, engine):
    """對應 T1"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    _insert_custom_table(engine, "合約資料表")
    _insert_custom_table(engine, "發票資料表")

    resp = client.get("/custom_table", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert isinstance(data, list)
    names = [d["name"] for d in data]
    assert "合約資料表" in names
    assert "發票資料表" in names
    # Check field_count present
    for item in data:
        assert "field_count" in item
        assert "description" in item


def test_list_custom_tables_keyword_filter(client, engine):
    """對應 T2"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    _insert_custom_table(engine, "合約資料表")
    _insert_custom_table(engine, "發票資料表")

    resp = client.get("/custom_table?keyword=合約", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    names = [d["name"] for d in data]
    assert "合約資料表" in names
    assert "發票資料表" not in names


def test_list_custom_tables_no_permission_returns_403(client, engine):
    """對應 T3"""
    user_id = _setup_plain_user(engine, "plain1_ct@test.com")

    resp = client.get("/custom_table", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# POST /custom_table — T4, T5, T6, T7, T8
# ---------------------------------------------------------------------------


def test_add_custom_table_returns_201(client, engine):
    """對應 T4"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)

    payload = {
        "name": "新增測試表格",
        "description": "測試說明",
        "fields": [
            {"field_name": "姓名", "field_type": "string"},
            {"field_name": "金額", "field_type": "number"},
        ],
    }
    resp = client.post("/custom_table", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    # Verify DB
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    table = db.query(CustomTable).filter(CustomTable.name == "新增測試表格").first()
    assert table is not None
    fields = (
        db.query(CustomTableField).filter(CustomTableField.table_id == table.id).all()
    )
    assert len(fields) == 2
    db.close()


def test_add_custom_table_empty_name_returns_400(client, engine):
    """對應 T5"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)

    payload = {
        "name": "",
        "fields": [{"field_name": "欄位", "field_type": "string"}],
    }
    resp = client.post("/custom_table", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "表格名稱為必填"


def test_add_custom_table_duplicate_name_returns_400(client, engine):
    """對應 T6"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    _insert_custom_table(engine, "重複表格")

    payload = {
        "name": "重複表格",
        "fields": [{"field_name": "欄位", "field_type": "string"}],
    }
    resp = client.post("/custom_table", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "表格名稱已存在"


def test_add_custom_table_empty_fields_returns_400(client, engine):
    """對應 T7"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)

    payload = {
        "name": "空欄位表格",
        "fields": [],
    }
    resp = client.post("/custom_table", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "至少須定義一個欄位"


def test_add_custom_table_empty_field_name_returns_400(client, engine):
    """對應 T8"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)

    payload = {
        "name": "欄位名稱空白",
        "fields": [{"field_name": "", "field_type": "string"}],
    }
    resp = client.post("/custom_table", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "欄位名稱不可為空"


# ---------------------------------------------------------------------------
# PATCH /custom_table/{id} — T9, T10, T11, T12
# ---------------------------------------------------------------------------


def test_update_custom_table_no_records_returns_200(client, engine):
    """對應 T9"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(
        engine, "修改測試", [{"field_name": "欄位A", "field_type": "string"}]
    )

    payload = {
        "name": "修改後表格",
        "description": "更新說明",
        "fields": [
            {"field_name": "欄位A", "field_type": "string"},
            {"field_name": "欄位B", "field_type": "number"},
        ],
    }
    resp = client.patch(
        f"/custom_table/{table_id}", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    # Verify fields replaced
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    fields = (
        db.query(CustomTableField).filter(CustomTableField.table_id == table_id).all()
    )
    assert len(fields) == 2
    db.close()


def test_update_custom_table_delete_field_with_records_returns_400(client, engine):
    """對應 T10"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(
        engine,
        "有紀錄表格",
        [
            {"field_name": "欄位A", "field_type": "string"},
            {"field_name": "欄位B", "field_type": "number"},
        ],
    )
    _insert_record(engine, table_id, {"欄位A": "test", "欄位B": 1})

    # Try to update removing 欄位B
    payload = {
        "name": "有紀錄表格",
        "fields": [{"field_name": "欄位A", "field_type": "string"}],
    }
    resp = client.patch(
        f"/custom_table/{table_id}", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "已有資料的欄位不可刪除"


def test_update_custom_table_add_field_with_records_returns_200(client, engine):
    """對應 T11"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(
        engine, "新增欄位測試", [{"field_name": "欄位A", "field_type": "string"}]
    )
    _insert_record(engine, table_id, {"欄位A": "test"})

    # Add 欄位B, keep 欄位A
    payload = {
        "name": "新增欄位測試",
        "fields": [
            {"field_name": "欄位A", "field_type": "string"},
            {"field_name": "欄位B", "field_type": "number"},
        ],
    }
    resp = client.patch(
        f"/custom_table/{table_id}", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    fields = (
        db.query(CustomTableField).filter(CustomTableField.table_id == table_id).all()
    )
    assert len(fields) == 2
    db.close()


def test_update_custom_table_not_found_returns_404(client, engine):
    """對應 T12"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)

    payload = {
        "name": "不存在",
        "fields": [{"field_name": "欄位", "field_type": "string"}],
    }
    resp = client.patch(
        "/custom_table/99999", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "資料表不存在"


# ---------------------------------------------------------------------------
# DELETE /custom_table/{id} — T13, T14, T15
# ---------------------------------------------------------------------------


def test_delete_custom_table_returns_200(client, engine):
    """對應 T13"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(engine, "刪除測試表格")

    resp = client.delete(f"/custom_table/{table_id}", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    # Verify removed
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    assert db.query(CustomTable).filter(CustomTable.id == table_id).first() is None
    assert (
        db.query(CustomTableField).filter(CustomTableField.table_id == table_id).count()
        == 0
    )
    db.close()


def test_delete_custom_table_bound_to_tool_returns_400(client, engine):
    """對應 T14"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(engine, "被綁定表格")

    # Bind a tool to this table
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    db.add(
        Tool(
            name="綁定工具T14",
            tool_type="image_extract",
            custom_table_id=table_id,
            auth_type="none",
        )
    )
    db.commit()
    db.close()

    resp = client.delete(f"/custom_table/{table_id}", headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "此資料表已被工具綁定，無法刪除"


def test_delete_custom_table_not_found_returns_404(client, engine):
    """對應 T15"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)

    resp = client.delete("/custom_table/99999", headers=_auth_headers(admin_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "資料表不存在"


# ---------------------------------------------------------------------------
# GET /custom_table/options — T16, T17
# ---------------------------------------------------------------------------


def test_list_custom_table_options_returns_200(client, engine):
    """對應 T16"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    _insert_custom_table(
        engine,
        "選單表格A",
        [
            {"field_name": "名稱", "field_type": "string"},
            {"field_name": "數量", "field_type": "number"},
        ],
    )
    _insert_custom_table(
        engine, "選單表格B", [{"field_name": "項目", "field_type": "string"}]
    )

    resp = client.get("/custom_table/options", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert isinstance(data, list)
    names = [d["name"] for d in data]
    assert "選單表格A" in names
    assert "選單表格B" in names

    table_a = next(d for d in data if d["name"] == "選單表格A")
    assert "fields" in table_a
    assert len(table_a["fields"]) == 2
    for f in table_a["fields"]:
        assert "field_name" in f
        assert "field_type" in f


def test_list_custom_table_options_unauthenticated_returns_401(client, engine):
    """對應 T17"""
    resp = client.get("/custom_table/options")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /custom_table/{id}/records — T18, T19, T20
# ---------------------------------------------------------------------------


def test_list_records_returns_200_with_fields_and_records(client, engine):
    """對應 T18"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(
        engine,
        "Records表格T18",
        [
            {"field_name": "姓名", "field_type": "string"},
            {"field_name": "金額", "field_type": "number"},
        ],
    )
    _insert_record(engine, table_id, {"姓名": "Alice", "金額": 100})
    _insert_record(engine, table_id, {"姓名": "Bob", "金額": 200})

    resp = client.get(f"/custom_table/{table_id}/records", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert "fields" in body
    assert "records" in body
    assert len(body["fields"]) == 2
    assert len(body["records"]) == 2
    field_names = [f["field_name"] for f in body["fields"]]
    assert "姓名" in field_names
    assert "金額" in field_names
    for r in body["records"]:
        assert "id" in r
        assert "data" in r
        assert "created_at" in r


def test_list_records_table_not_found_returns_404(client, engine):
    """對應 T19"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)

    resp = client.get("/custom_table/99999/records", headers=_auth_headers(admin_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "資料表不存在"


def test_list_records_no_permission_returns_403(client, engine):
    """對應 T20"""
    user_id = _setup_plain_user(engine, "plain20_ct@test.com")
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(engine, "Records表格T20")

    resp = client.get(f"/custom_table/{table_id}/records", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# DELETE /custom_table/{id}/records/{record_id} — T21, T22
# ---------------------------------------------------------------------------


def test_delete_record_returns_200(client, engine):
    """對應 T21"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(engine, "Records表格T21")
    record_id = _insert_record_id(engine, table_id, {"欄位A": "test"})

    resp = client.delete(
        f"/custom_table/{table_id}/records/{record_id}",
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    assert db.query(CustomTableRecord).filter(CustomTableRecord.id == record_id).first() is None
    db.close()


def test_delete_record_not_found_returns_404(client, engine):
    """對應 T22"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(engine, "Records表格T22")

    resp = client.delete(
        f"/custom_table/{table_id}/records/99999",
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "記錄不存在"


# ---------------------------------------------------------------------------
# DELETE /custom_table/{id}/records — T23
# ---------------------------------------------------------------------------


def test_delete_all_records_returns_200(client, engine):
    """對應 T23"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _insert_custom_table(engine, "Records表格T23")
    _insert_record(engine, table_id, {"欄位A": "r1"})
    _insert_record(engine, table_id, {"欄位A": "r2"})
    _insert_record(engine, table_id, {"欄位A": "r3"})

    resp = client.delete(
        f"/custom_table/{table_id}/records",
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    count = db.query(CustomTableRecord).filter(CustomTableRecord.table_id == table_id).count()
    assert count == 0
    db.close()
