"""Pydantic schemas for fn_ai_partner_config API."""

from pydantic import BaseModel, Field


class AiPartnerCreate(BaseModel):
    """新增 AI 夥伴輸入。"""

    name: str = Field(..., description="夥伴名稱")
    description: str | None = Field(None, description="描述")
    role_definition: str | None = Field(None, description="角色定義")
    behavior_limit: str | None = Field(None, description="行為限制")
    tool_ids: list[int] = Field(default_factory=list, description="可用工具 id 陣列")


class AiPartnerUpdate(BaseModel):
    """修改 AI 夥伴輸入。"""

    name: str = Field(..., description="夥伴名稱")
    description: str | None = Field(None, description="描述")
    role_definition: str | None = Field(None, description="角色定義")
    behavior_limit: str | None = Field(None, description="行為限制")
    tool_ids: list[int] = Field(default_factory=list, description="可用工具 id 陣列")
    is_enabled: bool | None = Field(None, description="是否啟用")


class AiPartnerItem(BaseModel):
    """AI 夥伴清單單項輸出。"""

    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    is_enabled: bool
    role_definition: str | None
    behavior_limit: str | None
    tool_ids: list[int] = []


class ToolOptionItem(BaseModel):
    """工具選項清單單項輸出（供 AI 夥伴設定頁使用）。"""

    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
