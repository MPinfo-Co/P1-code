import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text

_MIGRATION_PATH = (
    Path(__file__).parent.parent
    / "alembic"
    / "versions"
    / "538d0579a48c_seed_initial_roles_and_admin.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("seed_migration", _MIGRATION_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_migration = _load_migration()


def _run_upgrade(engine):
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            _migration.upgrade()


def test_admin_login_success(client, engine):
    """對應 TestPlan T1"""
    _run_upgrade(engine)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@mpinfo.com.tw", "password": "admin123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_admin_login_wrong_password(client, engine):
    """對應 TestPlan T2"""
    _run_upgrade(engine)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@mpinfo.com.tw", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "帳號或密碼錯誤"


def test_seed_idempotent(engine):
    """對應 TestPlan T3"""
    _run_upgrade(engine)
    _run_upgrade(engine)

    with engine.connect() as conn:
        admin_role_count = conn.execute(
            text("SELECT COUNT(*) FROM roles WHERE name = 'admin'")
        ).scalar()
        user_role_count = conn.execute(
            text("SELECT COUNT(*) FROM roles WHERE name = 'user'")
        ).scalar()
        admin_user_count = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE email = 'admin@mpinfo.com.tw'")
        ).scalar()

    assert admin_role_count == 1
    assert user_role_count == 1
    assert admin_user_count == 1
