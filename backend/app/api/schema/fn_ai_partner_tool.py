"""Pydantic schemas for fn_ai_partner_tool API."""

from pydantic import BaseModel, Field


class ToolBodyParamCreate(BaseModel):
    """單筆 Body 參數輸入。"""

    param_name: str = Field(..., description="參數名稱")
    param_type: str = Field(..., description="型別：string / number / boolean / object")
    is_required: bool = Field(..., description="是否必填")
    description: str | None = Field(None, description="參數說明與範例值")


class ToolImageFieldCreate(BaseModel):
    """單筆圖片擷取欄位輸入（image_extract 類型使用）。"""

    field_name: str = Field(..., description="欄位名稱")
    field_type: str = Field(..., description="欄位型別：string / number / boolean")
    description: str | None = Field(None, description="欄位說明")


class ToolCreate(BaseModel):
    """新增工具輸入。"""

    name: str = Field(..., description="工具名稱")
    description: str | None = Field(None, description="工具說明")
    tool_type: str = Field(
        default="external_api",
        description="工具類型：external_api / image_extract / web_scraper",
    )
    endpoint_url: str | None = Field(
        None, description="API Endpoint URL（external_api 類型）"
    )
    http_method: str | None = Field(
        None, description="HTTP Method（external_api 類型）"
    )
    auth_type: str | None = Field(
        None, description="認證方式：none / api_key / bearer（external_api 類型）"
    )
    auth_header_name: str | None = Field(
        None, description="API Key 模式下的 Header 名稱"
    )
    credential: str | None = Field(None, description="憑證（明文，後端加密儲存）")
    body_params: list[ToolBodyParamCreate] = Field(
        default_factory=list, description="Body 參數定義（external_api 類型）"
    )
    image_fields: list[ToolImageFieldCreate] = Field(
        default_factory=list, description="圖片擷取欄位定義（image_extract 類型）"
    )
    target_url: str | None = Field(None, description="目標網址（web_scraper 類型）")
    extract_description: str | None = Field(
        None, description="擷取描述（web_scraper 類型）"
    )
    max_chars: int | None = Field(
        None, description="最大擷取字元數（web_scraper 類型，預設 4000）"
    )


class ToolUpdate(BaseModel):
    """修改工具輸入。"""

    name: str = Field(..., description="工具名稱")
    description: str | None = Field(None, description="工具說明")
    tool_type: str | None = Field(
        None, description="工具類型（後端忽略，以 DB 現有值為準）"
    )
    endpoint_url: str | None = Field(
        None, description="API Endpoint URL（external_api 類型）"
    )
    http_method: str | None = Field(
        None, description="HTTP Method（external_api 類型）"
    )
    auth_type: str | None = Field(
        None, description="認證方式：none / api_key / bearer（external_api 類型）"
    )
    auth_header_name: str | None = Field(
        None, description="API Key 模式下的 Header 名稱"
    )
    credential: str | None = Field(None, description="憑證（空白表示不變更）")
    body_params: list[ToolBodyParamCreate] = Field(
        default_factory=list, description="Body 參數定義（external_api 類型）"
    )
    image_fields: list[ToolImageFieldCreate] = Field(
        default_factory=list, description="圖片擷取欄位定義（image_extract 類型）"
    )
    target_url: str | None = Field(None, description="目標網址（web_scraper 類型）")
    extract_description: str | None = Field(
        None, description="擷取描述（web_scraper 類型）"
    )
    max_chars: int | None = Field(
        None, description="最大擷取字元數（web_scraper 類型）"
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


class ToolImageFieldItem(BaseModel):
    """單筆圖片擷取欄位輸出（image_extract 類型）。"""

    model_config = {"from_attributes": True}

    id: int
    field_name: str
    field_type: str
    description: str | None
    sort_order: int


class ToolWebScraperConfigItem(BaseModel):
    """網頁擷取設定輸出（web_scraper 類型）。"""

    model_config = {"from_attributes": True}

    target_url: str
    extract_description: str
    max_chars: int


class ToolItem(BaseModel):
    """工具清單單項輸出。"""

    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    tool_type: str
    endpoint_url: str | None
    http_method: str | None
    auth_type: str
    auth_header_name: str | None
    has_credential: bool
    body_params: list[ToolBodyParamItem] = []
    image_fields: list[ToolImageFieldItem] = []
    web_scraper_config: ToolWebScraperConfigItem | None = None


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
