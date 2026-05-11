"""Pydantic schemas for fn_feedback API."""

from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackSubmit(BaseModel):
    """提交回饋輸入。"""

    rating: int | None = Field(None, description="評分，1 至 5 星")
    comment: str | None = Field(None, description="文字留言")


class FeedbackListItem(BaseModel):
    """回饋列表單項輸出。"""

    model_config = {"from_attributes": True}

    id: int
    user_name: str | None
    rating: int
    comment_summary: str | None
    created_at: datetime
