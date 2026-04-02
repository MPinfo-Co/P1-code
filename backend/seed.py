"""
初始資料腳本
執行方式：python seed.py
用途：建立預設角色與第一個 admin 帳號
注意：請在首次部署後立即修改 admin 密碼
"""

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import Role, User, UserRole

DEFAULT_ROLES = [
    {
        "name": "admin",
        "can_access_ai": True,
        "can_use_kb": True,
        "can_manage_accounts": True,
        "can_manage_roles": True,
        "can_edit_ai": True,
        "can_manage_kb": True,
    },
    {
        "name": "user",
        "can_access_ai": True,
        "can_use_kb": True,
        "can_manage_accounts": False,
        "can_manage_roles": False,
        "can_edit_ai": False,
        "can_manage_kb": False,
    },
]

ADMIN_EMAIL = "admin@mpinfo.com.tw"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "Admin"


def seed():
    db = SessionLocal()
    try:
        # 建立預設角色
        for role_data in DEFAULT_ROLES:
            existing = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not existing:
                db.add(Role(**role_data))
                print(f"建立角色：{role_data['name']}")
            else:
                print(f"角色已存在，略過：{role_data['name']}")
        db.commit()

        # 建立 admin 帳號
        existing_user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not existing_user:
            admin_user = User(
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                is_active=True,
            )
            db.add(admin_user)
            db.flush()

            admin_role = db.query(Role).filter(Role.name == "admin").first()
            db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
            db.commit()
            print(f"建立 admin 帳號：{ADMIN_EMAIL}")
        else:
            print(f"admin 帳號已存在，略過：{ADMIN_EMAIL}")

        print("Seed 完成")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
