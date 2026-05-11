"""
Pagination tests for Issue-259 (SD-259):
  GET /user?page=&page_size=
  GET /roles?page=&page_size=
  GET /events?page=&page_size=

Covers: page/page_size boundaries, last-page partial slice,
page out of range, filter + paginate consistency (T1-T8 from TDD).

Note: events tests require a real PostgreSQL DB (JSONB columns) and are
skipped automatically when DATABASE_URL points at SQLite (in-memory).
"""

import os
import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.utils.util_store import create_access_token, hash_password
from app.db.models.function_access import (
    FunctionItems as Function,
    FunctionFolder,
    RoleFunction,
)
from app.db.models.user_role import Role, User, UserRole

# Events model uses JSONB (PostgreSQL-only); skip events tests on SQLite
_USE_SQLITE = os.environ.get("DATABASE_URL", "sqlite:///:memory:").startswith("sqlite")

try:
    from app.db.models.events import SecurityEvent
    _EVENTS_AVAILABLE = True
except Exception:
    _EVENTS_AVAILABLE = False

requires_pg = pytest.mark.skipif(
    _USE_SQLITE,
    reason="SecurityEvent uses JSONB — requires PostgreSQL, skipped on SQLite in-memory",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_folder(db: Session, name: str = "設定", sort_order: int = 2) -> int:
    folder = FunctionFolder(folder_code=name, folder_label=name, sort_order=sort_order)
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db: Session, code: str, folder_id: int, sort_order: int = 1) -> int:
    fn = Function(
        function_code=code,
        function_label=code,
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


def _make_user(db: Session, email: str, name: str = "User", password: str = "password123") -> int:
    user = User(name=name, email=email, password_hash=hash_password(password))
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


def _setup_admin_with_perms(engine, *fn_codes) -> tuple[int, int]:
    """Create admin user + role with all specified function permissions."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db, "管理", 1)
    role_id = _make_role(db, "admin_pg_test")
    user_id = _make_user(db, "admin_pg@test.com", name="Admin PG")
    _assign_role(db, user_id, role_id)
    for code in fn_codes:
        fn_id = _make_function(db, code, folder_id)
        _grant_function(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, role_id


def _create_extra_users(engine, count: int, role_id: int) -> list[int]:
    """Create `count` extra users and assign them to role_id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    ids = []
    for i in range(count):
        uid = _make_user(db, f"extra_user_{i}@test.com", name=f"Extra {i}")
        _assign_role(db, uid, role_id)
        ids.append(uid)
    db.commit()
    db.close()
    return ids


def _create_extra_roles(engine, count: int) -> list[int]:
    """Create `count` extra roles."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    ids = []
    for i in range(count):
        rid = _make_role(db, f"extra_role_{i}")
        ids.append(rid)
    db.commit()
    db.close()
    return ids


def _create_security_events(engine, count: int) -> None:
    """Create `count` security events (requires PostgreSQL for JSONB)."""
    SecurityEvent.__table__.create(bind=engine, checkfirst=True)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    for i in range(count):
        evt = SecurityEvent(
            event_date=f"2026-01-{(i % 28) + 1:02d}",
            star_rank=(i % 5) + 1,
            title=f"Test Event {i}",
            affected_summary=f"Host-{i}",
            current_status="pending",
            match_key=f"key_{i}",
            detection_count=1,
        )
        db.add(evt)
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# GET /user — pagination
# ---------------------------------------------------------------------------


def test_user_list_first_page(client, engine):
    """T1: 25 users, page=1, page_size=10 → 10 items, total=25."""
    admin_id, role_id = _setup_admin_with_perms(engine, "fn_user")
    # admin itself is 1 user; add 24 more
    _create_extra_users(engine, 24, role_id)

    resp = client.get("/user?page=1&page_size=10", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 25
    assert len(body["items"]) == 10
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["total_pages"] == 3


def test_user_list_last_page_partial(client, engine):
    """T2: 25 users, page=3, page_size=10 → 5 items (partial last page)."""
    admin_id, role_id = _setup_admin_with_perms(engine, "fn_user")
    _create_extra_users(engine, 24, role_id)

    resp = client.get("/user?page=3&page_size=10", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 25
    assert len(body["items"]) == 5
    assert body["page"] == 3
    assert body["total_pages"] == 3


def test_user_list_page_beyond_range_returns_empty(client, engine):
    """Page beyond total_pages returns empty items but 200 OK."""
    admin_id, role_id = _setup_admin_with_perms(engine, "fn_user")
    _create_extra_users(engine, 4, role_id)  # total = 5

    resp = client.get("/user?page=99&page_size=10", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 0
    assert body["total_pages"] == 1


def test_user_list_default_pagination(client, engine):
    """No page/page_size params → defaults (page=1, page_size=10) apply."""
    admin_id, role_id = _setup_admin_with_perms(engine, "fn_user")

    resp = client.get("/user", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert "total_pages" in body
    assert body["page"] == 1
    assert body["page_size"] == 10


def test_user_list_filter_and_paginate(client, engine):
    """Filter by role_id + page — total reflects filtered set."""
    admin_id, role_id = _setup_admin_with_perms(engine, "fn_user")

    # Create a second role with 5 users
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    other_role_id = _make_role(db, "viewer_pg_test")
    for i in range(5):
        uid = _make_user(db, f"viewer_{i}@test.com", name=f"Viewer {i}")
        _assign_role(db, uid, other_role_id)
    db.commit()
    db.close()

    resp = client.get(
        f"/user?role_id={other_role_id}&page=1&page_size=3",
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 3
    assert body["total_pages"] == 2


def test_user_list_unauthenticated_returns_401(client, engine):
    """T3a: no token → 401."""
    resp = client.get("/user?page=1&page_size=10")
    assert resp.status_code == 401


def test_user_list_no_permission_returns_403(client, engine):
    """T3b: logged in but lacks fn_user → 403."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "noperm_role_u")
    user_id = _make_user(db, "noperm_user@test.com")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()

    resp = client.get("/user?page=1&page_size=10", headers=_auth_headers(user_id))
    assert resp.status_code == 403


def test_user_list_invalid_page_returns_400(client, engine):
    """T3c: page=-1 → 400 (FastAPI 422 normalised to 400 by middleware)."""
    admin_id, _ = _setup_admin_with_perms(engine, "fn_user")
    resp = client.get("/user?page=-1&page_size=10", headers=_auth_headers(admin_id))
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /roles — pagination
# ---------------------------------------------------------------------------


def test_roles_list_first_page(client, engine):
    """T4: 15 roles, page=1, page_size=5 → 5 items, total=15."""
    admin_id, _ = _setup_admin_with_perms(engine, "fn_role")
    # admin_pg_test role = 1 role; add 14 more
    _create_extra_roles(engine, 14)

    resp = client.get("/roles?page=1&page_size=5", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 15
    assert len(body["items"]) == 5
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert body["total_pages"] == 3


def test_roles_list_last_page_partial(client, engine):
    """T5: 15 roles, page=3, page_size=5 → 5 items on last page."""
    admin_id, _ = _setup_admin_with_perms(engine, "fn_role")
    _create_extra_roles(engine, 14)

    resp = client.get("/roles?page=3&page_size=5", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 15
    assert len(body["items"]) == 5
    assert body["page"] == 3


def test_roles_list_default_pagination(client, engine):
    """T6: no params → defaults apply, paginated structure returned."""
    admin_id, _ = _setup_admin_with_perms(engine, "fn_role")

    resp = client.get("/roles", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert "total_pages" in body


def test_roles_list_keyword_filter_and_paginate(client, engine):
    """Filter + paginate: only matching roles counted in total."""
    admin_id, _ = _setup_admin_with_perms(engine, "fn_role")

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    for i in range(6):
        _make_role(db, f"alpha_role_{i}")
    for i in range(3):
        _make_role(db, f"beta_role_{i}")
    db.commit()
    db.close()

    resp = client.get("/roles?keyword=alpha&page=1&page_size=4", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 6
    assert len(body["items"]) == 4
    assert body["total_pages"] == 2


def test_roles_list_unauthenticated_returns_401(client, engine):
    """T6a: no token → 401."""
    resp = client.get("/roles?page=1&page_size=5")
    assert resp.status_code == 401


def test_roles_list_no_permission_returns_403(client, engine):
    """T6b: logged in but lacks fn_role → 403."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "noperm_role_r")
    user_id = _make_user(db, "noperm_roles@test.com")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()

    resp = client.get("/roles?page=1&page_size=5", headers=_auth_headers(user_id))
    assert resp.status_code == 403


def test_roles_list_invalid_page_returns_400(client, engine):
    """T6c: page=-1 → 400 (FastAPI 422 normalised to 400 by middleware)."""
    admin_id, _ = _setup_admin_with_perms(engine, "fn_role")
    resp = client.get("/roles?page=-1&page_size=5", headers=_auth_headers(admin_id))
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /events — pagination (events already had partial pagination; verify total_pages)
# ---------------------------------------------------------------------------


@requires_pg
def test_events_list_first_page(client, engine):
    """T7: 50 events, page=1, page_size=20 → 20 items, total=50, total_pages=3."""
    _create_security_events(engine, 50)
    admin_id, _ = _setup_admin_with_perms(engine, "fn_expert")

    resp = client.get("/events?page=1&page_size=20", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 50
    assert len(body["items"]) == 20
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total_pages"] == 3


@requires_pg
def test_events_list_last_page_partial(client, engine):
    """T8: 50 events, page=3, page_size=20 → 10 items on last page."""
    _create_security_events(engine, 50)
    admin_id, _ = _setup_admin_with_perms(engine, "fn_expert")

    resp = client.get("/events?page=3&page_size=20", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 50
    assert len(body["items"]) == 10
    assert body["page"] == 3
    assert body["total_pages"] == 3


@requires_pg
def test_events_list_has_total_pages_field(client, engine):
    """EventListResponse now includes total_pages field."""
    _create_security_events(engine, 5)
    admin_id, _ = _setup_admin_with_perms(engine, "fn_expert")

    resp = client.get("/events?page=1&page_size=10", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert "total_pages" in body
    assert body["total_pages"] == 1


@requires_pg
def test_events_single_page_total_pages_is_one(client, engine):
    """total_pages is min 1 even when total=0."""
    admin_id, _ = _setup_admin_with_perms(engine, "fn_expert")

    resp = client.get("/events?page=1&page_size=20", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["total_pages"] == 1


@requires_pg
def test_events_filter_and_paginate(client, engine):
    """Filter by status + paginate — total reflects filtered set only."""
    _create_security_events(engine, 10)
    admin_id, _ = _setup_admin_with_perms(engine, "fn_expert")

    # Patch 3 events to 'resolved' status
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    evts = db.query(SecurityEvent).limit(3).all()
    for e in evts:
        e.current_status = "resolved"
    db.commit()
    db.close()

    resp = client.get("/events?status=resolved&page=1&page_size=5", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["total_pages"] == 1
