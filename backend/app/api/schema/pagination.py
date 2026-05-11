"""Generic paginated response schema and concrete resource aliases."""

from __future__ import annotations

from math import ceil
from typing import Generic, List, TypeVar

from pydantic import BaseModel, model_validator

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated list endpoints.

    Fields
    ------
    items      : slice of records for the current page
    total      : total number of records matching the query (before paging)
    page       : current 1-based page number
    page_size  : number of records per page
    total_pages: ``max(1, ceil(total / page_size))``
    """

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @model_validator(mode="before")
    @classmethod
    def _compute_total_pages(cls, values: dict) -> dict:
        """Auto-compute total_pages when not explicitly supplied."""
        if "total_pages" not in values or values.get("total_pages") is None:
            total = values.get("total", 0)
            page_size = values.get("page_size", 1) or 1
            values["total_pages"] = max(1, ceil(total / page_size))
        return values


# ---------------------------------------------------------------------------
# Concrete aliases (import these in API modules)
# ---------------------------------------------------------------------------

from app.api.schema.user import UserItem  # noqa: E402
from app.api.schema.roles import RoleItem  # noqa: E402
from app.api.schema.events import EventSummary  # noqa: E402


class PaginatedUserResponse(PaginatedResponse[UserItem]):
    """Paginated response for GET /api/user."""


class PaginatedRoleResponse(PaginatedResponse[RoleItem]):
    """Paginated response for GET /api/roles."""


class PaginatedEventResponse(PaginatedResponse[EventSummary]):
    """Paginated response for GET /api/events."""
