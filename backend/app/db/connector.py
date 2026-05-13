"""PostgreSQL connector: sync SQLAlchemy engine, session factory, and FastAPI dependency."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Iterator[Session]:
    """Yield a request-scoped SQLAlchemy session.

    Intended for use as a FastAPI dependency via `Depends(get_db)`. The
    session is closed automatically once the dependent endpoint returns.

    Args:
        None.

    Yields:
        Session: A SQLAlchemy session bound to the configured PostgreSQL
            engine.

    Returns:
        None: The function is a generator and yields rather than returns.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_with_tenant(request: Request) -> Iterator[Session]:
    """Yield a request-scoped SQLAlchemy session with tenant RLS context.

    在 session 連線後立即執行 `SET LOCAL app.current_tenant = '{tenant_id}'`，
    確保 PostgreSQL RLS POLICY 正確隔離租戶資料。

    tenant_id 由 TenantMiddleware 解析後存入 `request.state.tenant_id`。
    若 tenant_id 為 None（未認證請求），不設定 session variable，RLS 攔截所有存取。

    Args:
        request: The FastAPI/Starlette request carrying `state.tenant_id`.

    Yields:
        Session: A SQLAlchemy session with tenant context set.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    db = SessionLocal()
    try:
        if tenant_id is not None:
            db.execute(text(f"SET LOCAL app.current_tenant = '{int(tenant_id)}'"))
        yield db
    finally:
        db.close()
