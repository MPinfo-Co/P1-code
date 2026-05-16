"""
Tests for fn_custom_table_data_input APIs:
  GET    /custom_table_data_input/tables
  GET    /custom_table_data_input/options
  GET    /custom_table_data_input/tables/{id}/records
  POST   /custom_table_data_input/tables/{id}/records
  DELETE /custom_table_data_input/tables/{id}/records/{record_id}
  POST   /custom_table_data_input/tables/{id}/import
  GET    /custom_table_data_input/tables/{id}/format
"""

import io

from openpyxl import Workbook
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_custom_table import (
    CustomTable,
    CustomTableField,
    CustomTableRecord,
    RoleCustomTable,
)
from app.db.models.function_access import (
    FunctionFolder,
    FunctionItems as Function,
    RoleFunction,
)
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_folder(db: Session, name: str = "設定") -> int:
    folder = FunctionFolder(folder_code=name, folder_label=name, sort_order=2)
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db: Session, code: str, folder_id: int) -> int:
    fn = Function(
        function_code=code,
        function_label=code,
        folder_id=folder_id,
        sort_order=1,
    )
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db: Session, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(db: Session, email: str, name: str = "Test") -> int:
    user = User(name=name, email=email, password_hash=hash_password("password"))
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _grant_function(db: Session, role_id: int, fn_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=fn_id))
    db.flush()


def _make_custom_table(db: Session, name: str, description: str = "") -> int:
    t = CustomTable(name=name, description=description)
    db.add(t)
    db.flush()
    return t.id


def _make_field(
    db: Session, table_id: int, field_name: str, field_type: str, sort_order: int = 0
) -> int:
    f = CustomTableField(
        table_id=table_id,
        field_name=field_name,
        field_type=field_type,
        sort_order=sort_order,
    )
    db.add(f)
    db.flush()
    return f.id


def _authorize_table(db: Session, role_id: int, table_id: int) -> None:
    db.add(RoleCustomTable(role_id=role_id, table_id=table_id))
    db.flush()


def _make_record(db: Session, table_id: int, user_id: int, data: dict) -> int:
    r = CustomTableRecord(table_id=table_id, data=data, updated_by=user_id)
    db.add(r)
    db.flush()
    return r.id


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_user_with_fn_permission(engine, email: str = "admin@test.com"):
    """Create a user with fn_custom_table_data_input permission and return (user_id, role_id, fn_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db)
    fn_id = _make_function(db, "fn_custom_table_data_input", folder_id)
    role_id = _make_role(db, f"role_{email}")
    user_id = _make_user(db, email)
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_id


def _setup_plain_user(engine, email: str = "plain@test.com"):
    """Create a user without any function permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, f"plain_{email}")
    user_id = _make_user(db, email)
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id, role_id


def _make_xlsx_bytes(headers: list[str], rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# GET /custom_table_data_input/tables — T1, T2, T3
# ---------------------------------------------------------------------------


def test_list_tables_returns_authorized_tables(client, engine):
    """對應 T1"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t1 = _make_custom_table(db, "表A", "描述A")
    t2 = _make_custom_table(db, "表B", "描述B")
    _authorize_table(db, role_id, t1)
    _authorize_table(db, role_id, t2)
    db.commit()
    db.close()

    resp = client.get("/custom_table_data_input/tables", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert len(body["data"]) == 2
    ids = {item["id"] for item in body["data"]}
    assert t1 in ids and t2 in ids


def test_list_tables_no_authorized_tables_returns_empty(client, engine):
    """對應 T2"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "empty@test.com")

    resp = client.get("/custom_table_data_input/tables", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_list_tables_unauthenticated_returns_401(client, engine):
    """對應 T3"""
    resp = client.get("/custom_table_data_input/tables")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /custom_table_data_input/tables/{id}/records — T4, T5
# ---------------------------------------------------------------------------


def test_list_records_returns_fields_and_records(client, engine):
    """對應 T4"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "rec@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "RecTable")
    _make_field(db, t_id, "姓名", "string", 0)
    _make_field(db, t_id, "年齡", "number", 1)
    _authorize_table(db, role_id, t_id)
    _make_record(db, t_id, user_id, {"姓名": "Alice", "年齡": 30})
    _make_record(db, t_id, user_id, {"姓名": "Bob", "年齡": 25})
    _make_record(db, t_id, user_id, {"姓名": "Carol", "年齡": 28})
    db.commit()
    db.close()

    resp = client.get(
        f"/custom_table_data_input/tables/{t_id}/records",
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert len(body["data"]["fields"]) == 2
    assert len(body["data"]["records"]) == 3


def test_list_records_unauthorized_table_returns_403(client, engine):
    """對應 T5"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "unauth@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "PrivateTable")
    # Do NOT authorize
    db.commit()
    db.close()

    resp = client.get(
        f"/custom_table_data_input/tables/{t_id}/records",
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# POST /custom_table_data_input/tables/{id}/records — T6, T7
# ---------------------------------------------------------------------------


def test_add_record_returns_201(client, engine):
    """對應 T6"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "add@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "AddTable")
    _make_field(db, t_id, "欄位A", "string", 0)
    _authorize_table(db, role_id, t_id)
    db.commit()
    db.close()

    payload = {"data": {"欄位A": "值A"}}
    resp = client.post(
        f"/custom_table_data_input/tables/{t_id}/records",
        json=payload,
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"


def test_add_record_invalid_number_field_returns_400(client, engine):
    """對應 T7"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "badnum@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "NumTable")
    _make_field(db, t_id, "數量", "number", 0)
    _authorize_table(db, role_id, t_id)
    db.commit()
    db.close()

    payload = {"data": {"數量": "abc"}}
    resp = client.post(
        f"/custom_table_data_input/tables/{t_id}/records",
        json=payload,
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 400
    assert "數量" in resp.json()["detail"]
    assert "須為數值" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# DELETE /custom_table_data_input/tables/{id}/records/{record_id} — T8, T9
# ---------------------------------------------------------------------------


def test_delete_record_returns_200(client, engine):
    """對應 T8"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "del@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "DelTable")
    _make_field(db, t_id, "名稱", "string", 0)
    _authorize_table(db, role_id, t_id)
    rec_id = _make_record(db, t_id, user_id, {"名稱": "test"})
    db.commit()
    db.close()

    resp = client.delete(
        f"/custom_table_data_input/tables/{t_id}/records/{rec_id}",
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"


def test_delete_record_not_found_returns_404(client, engine):
    """對應 T9"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "del404@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "Del404Table")
    _authorize_table(db, role_id, t_id)
    db.commit()
    db.close()

    resp = client.delete(
        f"/custom_table_data_input/tables/{t_id}/records/99999",
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "記錄不存在"


# ---------------------------------------------------------------------------
# POST /custom_table_data_input/tables/{id}/import — T10, T11, T12
# ---------------------------------------------------------------------------


def test_import_valid_xlsx_returns_200(client, engine):
    """對應 T10"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "import_ok@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "ImportOKTable")
    _make_field(db, t_id, "名稱", "string", 0)
    _make_field(db, t_id, "數量", "number", 1)
    _authorize_table(db, role_id, t_id)
    db.commit()
    db.close()

    content = _make_xlsx_bytes(
        ["名稱", "數量"],
        [["A", 10], ["B", 20], ["C", 30]],
    )
    resp = client.post(
        f"/custom_table_data_input/tables/{t_id}/import",
        files={
            "file": (
                "data.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "匯入成功"


def test_import_xlsx_with_invalid_rows_returns_400(client, engine):
    """對應 T11"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "import_err@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "ImportErrTable")
    _make_field(db, t_id, "名稱", "string", 0)
    _make_field(db, t_id, "數量", "number", 1)
    _authorize_table(db, role_id, t_id)
    db.commit()
    db.close()

    # Row 3 (index 2) and row 5 (index 4) have invalid number
    content = _make_xlsx_bytes(
        ["名稱", "數量"],
        [["A", 10], ["B", "invalid"], ["C", 30], ["D", "bad"], ["E", 50]],
    )
    resp = client.post(
        f"/custom_table_data_input/tables/{t_id}/import",
        files={
            "file": (
                "data.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 400
    assert "格式有誤" in resp.json()["detail"]


def test_import_non_xlsx_file_returns_400(client, engine):
    """對應 T12"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "import_bad@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "ImportBadTable")
    _authorize_table(db, role_id, t_id)
    db.commit()
    db.close()

    resp = client.post(
        f"/custom_table_data_input/tables/{t_id}/import",
        files={"file": ("data.csv", b"a,b\n1,2", "text/csv")},
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "僅接受 .xlsx 格式檔案"


# ---------------------------------------------------------------------------
# GET /custom_table_data_input/tables/{id}/format — T13, T13b, T13c
# ---------------------------------------------------------------------------


def test_download_format_returns_xlsx(client, engine):
    """對應 T13"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "fmt@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "FmtTable")
    _make_field(db, t_id, "姓名", "string", 0)
    _make_field(db, t_id, "年齡", "number", 1)
    _authorize_table(db, role_id, t_id)
    db.commit()
    db.close()

    resp = client.get(
        f"/custom_table_data_input/tables/{t_id}/format",
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 200
    assert (
        resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_download_format_table_not_found_returns_404(client, engine):
    """對應 T13b"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "fmt404@test.com")

    resp = client.get(
        "/custom_table_data_input/tables/99999/format",
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "資料表不存在"


def test_download_format_unauthorized_table_returns_403(client, engine):
    """對應 T13c"""
    user_id, role_id, _ = _setup_user_with_fn_permission(engine, "fmt403@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "FmtPrivate")
    # Not authorized
    db.commit()
    db.close()

    resp = client.get(
        f"/custom_table_data_input/tables/{t_id}/format",
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# GET /custom_table_data_input/options — T14, T15
# ---------------------------------------------------------------------------


def test_get_options_returns_all_tables(client, engine):
    """對應 T14"""
    user_id, _, _ = _setup_user_with_fn_permission(engine, "opt@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_custom_table(db, "OptTable1")
    _make_custom_table(db, "OptTable2")
    db.commit()
    db.close()

    resp = client.get(
        "/custom_table_data_input/options",
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    names = [item["name"] for item in body["data"]]
    assert "OptTable1" in names
    assert "OptTable2" in names


def test_get_options_unauthenticated_returns_401(client, engine):
    """對應 T15"""
    resp = client.get("/custom_table_data_input/options")
    assert resp.status_code == 401
