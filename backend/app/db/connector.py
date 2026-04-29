"""PostgreSQL connector: sync SQLAlchemy engine, session factory, and FastAPI dependency."""

from collections.abc import Iterator

from sqlalchemy import create_engine
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
