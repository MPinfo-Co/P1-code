"""seed admin role with fn_user and fn_role permissions

Revision ID: d2e3f4a5b6c1
Revises: c1d2e3f4a5b6
Create Date: 2026-04-29 17:58:23.170409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c1'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    admin = conn.execute(
        sa.text("SELECT id FROM roles WHERE name = 'admin'")
    ).fetchone()
    if not admin:
        return
    admin_id = admin[0]
    for fn_name in ("fn_user", "fn_role"):
        fn = conn.execute(
            sa.text("SELECT function_id FROM functions WHERE function_name = :name"),
            {"name": fn_name},
        ).fetchone()
        if not fn:
            continue
        exists = conn.execute(
            sa.text("SELECT 1 FROM role_functions WHERE role_id = :rid AND function_id = :fid"),
            {"rid": admin_id, "fid": fn[0]},
        ).fetchone()
        if not exists:
            conn.execute(
                sa.text("INSERT INTO role_functions (role_id, function_id) VALUES (:rid, :fid)"),
                {"rid": admin_id, "fid": fn[0]},
            )


def downgrade() -> None:
    conn = op.get_bind()
    admin = conn.execute(
        sa.text("SELECT id FROM roles WHERE name = 'admin'")
    ).fetchone()
    if not admin:
        return
    conn.execute(
        sa.text("DELETE FROM role_functions WHERE role_id = :rid"),
        {"rid": admin[0]},
    )
