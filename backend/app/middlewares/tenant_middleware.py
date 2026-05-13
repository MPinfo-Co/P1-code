"""Tenant isolation middleware.

從 JWT token 中解析使用者的 tenant_id，並以 SET LOCAL 將其注入 PostgreSQL
session variable `app.current_tenant`，使 RLS POLICY 能自動過濾跨租戶資料。

若請求未攜帶有效 JWT，不設定 session variable，RLS 會阻擋所有資料存取。
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from fastapi.security import HTTPAuthorizationCredentials

from app.db.connector import SessionLocal
from app.db.models.user_role import User
from app.utils.util_store import authenticate


class TenantMiddleware(BaseHTTPMiddleware):
    """在每個 DB 連線上注入 `app.current_tenant` session variable。

    執行流程：
    1. 從 Authorization header 解析 JWT，取得 user_id。
    2. 查詢 tb_users 取得該使用者的 tenant_id。
    3. 於請求 DB session 的 event hook 中執行 SET LOCAL app.current_tenant = '{tenant_id}'。
    4. 若 JWT 無效或不存在，略過設定，RLS 自動攔截所有資料存取。
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """解析 JWT 並設定 tenant_id 至 request.state，供後續 DB session 使用。

        Args:
            request: The incoming Starlette request.
            call_next: Callable that invokes the next middleware or route handler.

        Returns:
            Response: The downstream response.
        """
        tenant_id: int | None = None

        auth_header = request.headers.get("authorization") or ""
        if auth_header.lower().startswith("bearer "):
            creds = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=auth_header.split(" ", 1)[1],
            )
            with SessionLocal() as db:
                try:
                    auth_ctx = authenticate(creds, db)
                    user = db.query(User).filter(User.id == auth_ctx.user_id).first()
                    if user is not None:
                        tenant_id = user.tenant_id
                except Exception:
                    tenant_id = None

        # 將 tenant_id 存入 request.state，供 get_db_with_tenant dependency 使用
        request.state.tenant_id = tenant_id

        response = await call_next(request)
        return response
