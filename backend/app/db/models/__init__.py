"""SQLAlchemy declarative base and ORM model registry.

Importing this package eagerly registers every ORM class on `Base.metadata`,
which is what Alembic autogenerate consumes via `target_metadata = Base.metadata`.
"""

from .fn_user_role import Role, TokenBlacklist, User, UserRole
from .fn_expert_security_event import *
