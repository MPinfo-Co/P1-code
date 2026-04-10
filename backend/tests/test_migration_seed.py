from sqlalchemy import text

from app.db.seed import seed_admin, seed_roles


def test_admin_login_success(client, engine):
    """對應 TestPlan T1"""
    with engine.begin() as conn:
        seed_roles(conn)
        seed_admin(conn)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@mpinfo.com.tw", "password": "admin123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_admin_login_wrong_password(client, engine):
    """對應 TestPlan T2"""
    with engine.begin() as conn:
        seed_roles(conn)
        seed_admin(conn)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@mpinfo.com.tw", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "帳號或密碼錯誤"


def test_seed_idempotent(engine):
    """對應 TestPlan T3"""
    with engine.begin() as conn:
        seed_roles(conn)
        seed_admin(conn)

    with engine.begin() as conn:
        seed_roles(conn)
        seed_admin(conn)

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
