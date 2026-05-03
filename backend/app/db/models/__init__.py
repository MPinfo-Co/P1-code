"""SQLAlchemy declarative base and ORM model registry.

Importing this package eagerly registers every ORM class on `Base.metadata`,
which is what Alembic autogenerate consumes via `target_metadata = Base.metadata`.
"""

from .fn_user_role import Role as Role, TokenBlacklist as TokenBlacklist, User as User, UserRole as UserRole
from .fn_navbar import FunctionFolder as FunctionFolder, Function as Function, RoleFunction as RoleFunction
from .fn_expert_security_event import *  # noqa: F401, F403
