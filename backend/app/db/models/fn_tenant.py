"""ORM model for fn_tenant: tb_tenants (訂閱群組主表).

建立 tenant 時，SQLAlchemy event listener 會自動建立對應的 default_user，
帳號格式為 {tenant_id}_admin。
"""

from sqlalchemy import Integer, String, event
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Tenant(Base):
    """訂閱群組主表，對應 tb_tenants。"""

    __tablename__ = "tb_tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


@event.listens_for(Tenant, "after_insert")
def create_default_user_for_tenant(mapper, connection, target: Tenant) -> None:
    """在 tenant 建立後自動建立帳號 {tenant_id}_admin 的 default_user。

    使用 INSERT ... ON CONFLICT DO NOTHING 確保冪等性，
    重複呼叫不會產生重複 default_user。
    """
    from app.utils.util_store import hash_password

    username = f"{target.id}_admin"
    connection.execute(
        __import__("sqlalchemy").text(
            "INSERT INTO tb_users (name, email, password_hash, tenant_id) "
            "VALUES (:name, :email, :password_hash, :tenant_id) "
            "ON CONFLICT (email) DO NOTHING"
        ),
        {
            "name": username,
            "email": f"{username}@tenant.local",
            "password_hash": hash_password(username),
            "tenant_id": target.id,
        },
    )
