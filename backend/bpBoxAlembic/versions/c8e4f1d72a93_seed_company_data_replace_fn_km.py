"""Seed company_data and replace fn_km with fn_company_data

Revision ID: c8e4f1d72a93
Revises: 466b985000fb
Create Date: 2026-05-06 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


revision: str = "c8e4f1d72a93"
down_revision: Union[str, Sequence[str], None] = "466b985000fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DELETE FROM tb_role_function WHERE function_id = 2")
    op.execute("DELETE FROM tb_function_items WHERE function_code = 'fn_km'")

    # add_roles seeded function_items with hard-coded ids and never bumped the sequence,
    # so nextval() would return 1 and collide with fn_partner. Sync first.
    op.execute(
        "SELECT setval('tb_function_items_function_id_seq', "
        "COALESCE((SELECT MAX(function_id) FROM tb_function_items), 1))"
    )
    op.execute(
        "INSERT INTO tb_function_items (function_code, function_label, folder_id, sort_order) "
        "VALUES ('fn_company_data', '公司資料', 1, 2)"
    )
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) "
        "SELECT 1, function_id FROM tb_function_items WHERE function_code = 'fn_company_data'"
    )

    ai_partners = table(
        "tb_ai_partners",
        column("id", sa.Integer),
        column("name", sa.String),
        column("description", sa.Text),
        column("is_builtin", sa.Boolean),
        column("is_enabled", sa.Boolean),
    )
    op.bulk_insert(
        ai_partners,
        [
            {
                "id": 1,
                "name": "資安專家",
                "description": "排程、資料來源（syslog-ng Store Box）",
                "is_builtin": True,
                "is_enabled": True,
            },
        ],
    )

    company_data = table(
        "tb_company_data",
        column("id", sa.Integer),
        column("name", sa.String),
        column("content", sa.Text),
    )
    op.bulk_insert(
        company_data,
        [
            {
                "id": 1,
                "name": "公司網段",
                "content": (
                    "公司內網主要使用 192.168.0.0/16 網段；VPN 用戶端使用 172.18.0.0/16，亦屬授權內網。"
                    "任何來自非上述網段的請求應視為外部行為。\n"
                    "DMZ 對外服務固定為 192.168.10.30 (Web)、192.168.10.40 (Mail)，其餘對外連線需另行確認。"
                ),
            },
            {
                "id": 2,
                "name": "重要設備名單",
                "content": (
                    "DC-SVR-01：IP 192.168.10.20，Windows Server 2022，Domain Controller（主 DNS），"
                    "負責人 Dama Wang，位置 IDC 機房 B。\n"
                    "MPIDCFW：IP 192.168.1.1，FortiOS 7.4，主邊界防火牆，"
                    "負責人 Rex Shen，位置 IDC 機房 A。\n"
                    "WEB-SVR-01：IP 192.168.10.30，Ubuntu 22.04 LTS，DMZ Web 應用伺服器，"
                    "負責人 Frank Liu，位置 IDC 機房 B。"
                ),
            },
            {
                "id": 3,
                "name": "白名單",
                "content": (
                    "Windows 4625 登入失敗事件，若來源 IP 屬於內網（192.168.x.x）且帳號為服務帳號（svc_*），"
                    "視為已知正常，不需報警。\n"
                    "每月 1 號 02:00–04:00 的 svc_backup 大量 4624/4634 事件為定期備份排程。\n"
                    "來源 IP 192.168.1.100 的全網掃描為 IT 弱掃主機定期作業。"
                ),
            },
            {
                "id": 4,
                "name": "公司處置方法",
                "content": (
                    "FortiGate deny 內部廣播位址（dstport 137-139, 445）為網路廣播正常行為，不需報警。\n"
                    "FortiGate subtype=virus 但 action=blocked 表示已被防毒攔截，可降為 INFO 等級。\n"
                    "FortiGate level=notice 的 traffic log 為一般通過紀錄，量大時不視為事件。"
                ),
            },
        ],
    )

    op.execute(
        "INSERT INTO tb_partners_company_data (company_data_id, partner_id) VALUES "
        "(1, 1), (2, 1), (3, 1), (4, 1)"
    )

    # Same nextval-collision risk as tb_function_items above — sync these too
    # so future autoincrement inserts (e.g. user creates a new partner from UI) don't collide.
    for seq, tbl in (
        ("tb_ai_partners_id_seq", "tb_ai_partners"),
        ("tb_company_data_id_seq", "tb_company_data"),
    ):
        op.execute(f"SELECT setval('{seq}', (SELECT MAX(id) FROM {tbl}))")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM tb_partners_company_data WHERE company_data_id IN (1, 2, 3, 4)"
    )
    op.execute("DELETE FROM tb_company_data WHERE id IN (1, 2, 3, 4)")
    op.execute("DELETE FROM tb_ai_partners WHERE id = 1")

    op.execute(
        "DELETE FROM tb_role_function "
        "WHERE function_id IN (SELECT function_id FROM tb_function_items WHERE function_code = 'fn_company_data')"
    )
    op.execute("DELETE FROM tb_function_items WHERE function_code = 'fn_company_data'")

    op.execute(
        "INSERT INTO tb_function_items (function_id, function_code, function_label, folder_id, sort_order) "
        "VALUES (2, 'fn_km', '知識庫', 1, 2)"
    )
    op.execute("INSERT INTO tb_role_function (role_id, function_id) VALUES (1, 2)")
