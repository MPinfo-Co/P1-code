"""Pydantic schemas for fn_ai_partner_tool API."""

from pydantic import BaseModel, Field


class ToolBodyParamCreate(BaseModel):
    """單筆 Body 參數輸入。"""

    param_name: str = Field(..., description="參數名稱")
    param_type: str = Field(..., description="型別：string / number / boolean / object")
    is_required: bool = Field(..., description="是否必填")
    description: str | None = Field(None, description="參數說明與範例值")


class ToolCreate(BaseModel):
    """新增工具輸入。"""

    name: str = Field(..., description="工具名稱")
    description: str | None = Field(None, description="工具說明")
    endpoint_url: str = Field(..., description="API Endpoint URL")
    http_method: str = Field(..., description="HTTP Method")
    auth_type: str = Field(..., description="認證方式：none / api_key / bearer")
    auth_header_name: str | None = Field(
        None, description="API Key 模式下的 Header 名稱"
    )
    credential: str | None = Field(None, description="憑證（明文，後端加密儲存）")
    body_params: list[ToolBodyParamCreate] = Field(
        default_factory=list, description="Body 參數定義"
    )


class ToolUpdate(BaseModel):
    """修改工具輸入。"""

    name: str = Field(..., description="工具名稱")
    description: str | None = Field(None, description="工具說明")
    endpoint_url: str = Field(..., description="API Endpoint URL")
    http_method: str = Field(..., description="HTTP Method")
    auth_type: str = Field(..., description="認證方式：none / api_key / bearer")
    auth_header_name: str | None = Field(
        None, description="API Key 模式下的 Header 名稱"
    )
    credential: str | None = Field(None, description="憑證（空白表示不變更）")
    body_params: list[ToolBodyParamCreate] = Field(
        default_factory=list, description="Body 參數定義"
    )


class ToolBodyParamItem(BaseModel):
    """單筆 Body 參數輸出。"""

    model_config = {"from_attributes": True}

    id: int
    param_name: str
    param_type: str
    is_required: bool
    description: str | None
    sort_order: int


class ToolItem(BaseModel):
    """工具清單單項輸出。"""

    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    endpoint_url: str
    http_method: str
    auth_type: str
    auth_header_name: str | None
    has_credential: bool
    body_params: list[ToolBodyParamItem] = []


class ToolTestRequest(BaseModel):
    """測試工具連線輸入。"""

    endpoint_url: str = Field(..., description="API Endpoint URL")
    http_method: str = Field(..., description="HTTP Method")
    auth_type: str = Field(..., description="認證方式：none / api_key / bearer")
    auth_header_name: str | None = Field(
        None, description="API Key 模式下的 Header 名稱"
    )
    credential: str | None = Field(None, description="憑證")
    body_params_values: dict | None = Field(
        None, description="Body 參數值（key-value）"
    )
    tool_id: int | None = Field(None, description="指定工具 id 時使用 DB 儲存的憑證")


class ToolTestResult(BaseModel):
    """測試工具連線結果。"""

    http_status: int
    response_body: object
