"""/tool router — AI工具管理 (fn_ai_partner_tool)."""

import base64
import os

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.schema.fn_ai_partner_tool import (
    ToolCreate,
    ToolCustomTableFieldItem,
    ToolCustomTableItem,
    ToolItem,
    ToolTestRequest,
    ToolTestResult,
    ToolUpdate,
    ToolWebScraperConfigItem,
)
from app.config.settings import settings
from app.db.connector import get_db
from app.db.models.fn_ai_partner_tool import (
    Tool,
    ToolBodyParam,
    ToolWebScraperConfig,
)
from app.db.models.fn_custom_table import CustomTable, CustomTableField
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import UserRole
from app.logger_utils import get_system_logger
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/tool", tags=["fn_ai_partner_tool"])
system_logger = get_system_logger()

FN_TOOL_NAME = "fn_ai_partner_tool"

VALID_AUTH_TYPES = {"none", "api_key", "bearer"}
VALID_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE"}
VALID_TOOL_TYPES = {"external_api", "image_extract", "web_scraper"}


# ---------------------------------------------------------------------------
# GET /tool/options
# ---------------------------------------------------------------------------


@router.get("/options", status_code=status.HTTP_200_OK)
def list_tool_options(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Return all tools as options (id, name, description). Requires login only."""
    tools = db.query(Tool).order_by(Tool.name.asc()).all()
    data = [{"id": t.id, "name": t.name, "description": t.description} for t in tools]
    return {"message": "查詢成功", "data": data}


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------


def _has_fn_tool_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_tool function permission."""
    fn = (
        db.query(FunctionItems)
        .filter(FunctionItems.function_code == FN_TOOL_NAME)
        .first()
    )
    if fn is None:
        return False
    return (
        db.query(RoleFunction)
        .join(UserRole, RoleFunction.role_id == UserRole.role_id)
        .filter(
            UserRole.user_id == user_id,
            RoleFunction.function_id == fn.function_id,
        )
        .first()
        is not None
    )


# ---------------------------------------------------------------------------
# AES-256-GCM helpers
# ---------------------------------------------------------------------------

_AES_KEY_BYTES = 32  # 256 bits


def _derive_key() -> bytes:
    """Derive a 32-byte key from settings.aes_key."""
    raw = settings.aes_key.encode("utf-8")
    # Pad or truncate to 32 bytes
    return (raw * (_AES_KEY_BYTES // len(raw) + 1))[:_AES_KEY_BYTES]


def _encrypt(plain: str) -> str:
    """AES-256-GCM encrypt; returns base64-encoded nonce+ciphertext."""
    key = _derive_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce
    ciphertext = aesgcm.encrypt(nonce, plain.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def _decrypt(enc: str) -> str:
    """Decrypt base64-encoded nonce+ciphertext; returns plain text."""
    key = _derive_key()
    aesgcm = AESGCM(key)
    data = base64.b64decode(enc)
    nonce, ciphertext = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


# ---------------------------------------------------------------------------
# GET /tool
# ---------------------------------------------------------------------------


@router.get("", status_code=status.HTTP_200_OK)
def list_tools(
    keyword: str | None = Query(None, description="工具名稱關鍵字篩選（ILIKE）"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """List tools, optionally filtered by keyword. Requires fn_tool permission."""
    if not _has_fn_tool_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    query = db.query(Tool)
    if keyword:
        query = query.filter(Tool.name.ilike(f"%{keyword}%"))
    tools = query.order_by(Tool.created_at.asc()).all()

    tool_ids = [t.id for t in tools]

    # Load body params
    all_params = (
        (
            db.query(ToolBodyParam)
            .filter(ToolBodyParam.tool_id.in_(tool_ids))
            .order_by(ToolBodyParam.tool_id, ToolBodyParam.sort_order)
            .all()
        )
        if tool_ids
        else []
    )
    params_by_tool: dict[int, list] = {}
    for p in all_params:
        params_by_tool.setdefault(p.tool_id, []).append(p)

    # Load web scraper configs
    all_scraper_configs = (
        (
            db.query(ToolWebScraperConfig)
            .filter(ToolWebScraperConfig.tool_id.in_(tool_ids))
            .all()
        )
        if tool_ids
        else []
    )
    scraper_config_by_tool: dict[int, ToolWebScraperConfig] = {}
    for c in all_scraper_configs:
        scraper_config_by_tool[c.tool_id] = c

    # Load custom table info for image_extract tools
    custom_table_ids = [
        t.custom_table_id
        for t in tools
        if t.tool_type == "image_extract" and t.custom_table_id is not None
    ]
    custom_tables_map: dict[int, CustomTable] = {}
    custom_table_fields_map: dict[int, list] = {}
    if custom_table_ids:
        custom_tables = (
            db.query(CustomTable).filter(CustomTable.id.in_(custom_table_ids)).all()
        )
        for ct in custom_tables:
            custom_tables_map[ct.id] = ct
        all_ct_fields = (
            db.query(CustomTableField)
            .filter(CustomTableField.table_id.in_(custom_table_ids))
            .order_by(CustomTableField.table_id, CustomTableField.sort_order)
            .all()
        )
        for f in all_ct_fields:
            custom_table_fields_map.setdefault(f.table_id, []).append(f)

    items = []
    for t in tools:
        tool_type = t.tool_type or "external_api"

        # Build web_scraper_config if applicable
        web_scraper_config = None
        if tool_type == "web_scraper" and t.id in scraper_config_by_tool:
            sc = scraper_config_by_tool[t.id]
            web_scraper_config = ToolWebScraperConfigItem(
                target_url=sc.target_url,
                extract_description=sc.extract_description,
                max_chars=sc.max_chars,
            )

        # Build custom_table if applicable
        custom_table = None
        if tool_type == "image_extract" and t.custom_table_id is not None:
            ct = custom_tables_map.get(t.custom_table_id)
            if ct is not None:
                ct_fields = custom_table_fields_map.get(ct.id, [])
                custom_table = ToolCustomTableItem(
                    custom_table_id=ct.id,
                    name=ct.name,
                    fields=[
                        ToolCustomTableFieldItem(
                            field_name=f.field_name, field_type=f.field_type
                        )
                        for f in ct_fields
                    ],
                )

        item = ToolItem(
            id=t.id,
            name=t.name,
            description=t.description,
            tool_type=tool_type,
            endpoint_url=t.endpoint_url,
            http_method=t.http_method,
            auth_type=t.auth_type,
            auth_header_name=t.auth_header_name,
            has_credential=t.credential_enc is not None,
            body_params=params_by_tool.get(t.id, []),
            custom_table=custom_table,
            web_scraper_config=web_scraper_config,
        )
        items.append(item)

    return {"message": "查詢成功", "data": [i.model_dump() for i in items]}


# ---------------------------------------------------------------------------
# POST /tool
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
def add_tool(
    payload: ToolCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Create a new tool. Requires fn_tool permission."""
    if not _has_fn_tool_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # Common validation
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="工具名稱為必填"
        )
    if len(payload.name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="工具名稱不可超過 100 字"
        )
    if db.query(Tool).filter(Tool.name == payload.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="工具名稱已存在"
        )

    tool_type = payload.tool_type or "external_api"
    if tool_type not in VALID_TOOL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="工具類型不合法"
        )

    if tool_type == "external_api":
        # Validate external_api fields
        if not payload.endpoint_url or not payload.endpoint_url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API Endpoint URL 為必填",
            )
        auth_type = payload.auth_type or "none"
        if auth_type not in VALID_AUTH_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="認證方式不合法"
            )
        if auth_type == "api_key" and (
            not payload.auth_header_name or not payload.auth_header_name.strip()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API Key 模式下 Header 名稱為必填",
            )
        if auth_type in {"api_key", "bearer"} and (
            not payload.credential or not payload.credential.strip()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="憑證為必填"
            )
        http_method = payload.http_method or ""
        if http_method not in VALID_HTTP_METHODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP Method 不合法"
            )

    elif tool_type == "image_extract":
        # Validate image_extract: must have custom_table_id
        if payload.custom_table_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="圖片擷取工具必須綁定自訂表格",
            )
        ct = (
            db.query(CustomTable)
            .filter(CustomTable.id == payload.custom_table_id)
            .first()
        )
        if ct is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的自訂資料表不存在",
            )

    elif tool_type == "web_scraper":
        # Validate web_scraper fields
        if not payload.target_url or not payload.target_url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="目標網址為必填"
            )
        if not payload.extract_description or not payload.extract_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="擷取描述為必填"
            )

    # Create tool
    if tool_type == "external_api":
        auth_type_val = payload.auth_type or "none"
        credential_enc = _encrypt(payload.credential) if payload.credential else None
        tool = Tool(
            name=payload.name,
            description=payload.description,
            tool_type=tool_type,
            endpoint_url=payload.endpoint_url,
            http_method=payload.http_method,
            auth_type=auth_type_val,
            auth_header_name=payload.auth_header_name,
            credential_enc=credential_enc,
        )
    elif tool_type == "image_extract":
        tool = Tool(
            name=payload.name,
            description=payload.description,
            tool_type=tool_type,
            custom_table_id=payload.custom_table_id,
            endpoint_url=None,
            http_method=None,
            auth_type="none",
            auth_header_name=None,
            credential_enc=None,
        )
    else:  # web_scraper
        tool = Tool(
            name=payload.name,
            description=payload.description,
            tool_type=tool_type,
            endpoint_url=None,
            http_method=None,
            auth_type="none",
            auth_header_name=None,
            credential_enc=None,
        )

    db.add(tool)
    db.flush()

    if tool_type == "external_api":
        for idx, param in enumerate(payload.body_params or []):
            db.add(
                ToolBodyParam(
                    tool_id=tool.id,
                    param_name=param.param_name,
                    param_type=param.param_type,
                    is_required=param.is_required,
                    description=param.description,
                    sort_order=idx,
                )
            )
    elif tool_type == "web_scraper":
        db.add(
            ToolWebScraperConfig(
                tool_id=tool.id,
                target_url=payload.target_url,
                extract_description=payload.extract_description,
                max_chars=payload.max_chars if payload.max_chars is not None else 4000,
            )
        )

    db.commit()
    system_logger.info(f"User {auth.user_id} created tool {tool.id} ({tool.name})")
    return {"message": "新增成功"}


# ---------------------------------------------------------------------------
# PATCH /tool/{id}
# ---------------------------------------------------------------------------


@router.patch("/{tool_id}", status_code=status.HTTP_200_OK)
def update_tool(
    tool_id: int,
    payload: ToolUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Update a tool. Requires fn_tool permission."""
    if not _has_fn_tool_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工具不存在")

    # tool_type is immutable — always use DB value
    tool_type = tool.tool_type or "external_api"

    # Common validation
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="工具名稱為必填"
        )
    if len(payload.name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="工具名稱不可超過 100 字"
        )
    conflict = (
        db.query(Tool).filter(Tool.name == payload.name, Tool.id != tool_id).first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="工具名稱已存在"
        )

    if tool_type == "external_api":
        if not payload.endpoint_url or not payload.endpoint_url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API Endpoint URL 為必填",
            )
        auth_type = payload.auth_type or "none"
        if auth_type not in VALID_AUTH_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="認證方式不合法"
            )
        if auth_type == "api_key" and (
            not payload.auth_header_name or not payload.auth_header_name.strip()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API Key 模式下 Header 名稱為必填",
            )
        http_method = payload.http_method or ""
        if http_method not in VALID_HTTP_METHODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP Method 不合法"
            )

    elif tool_type == "image_extract":
        if payload.custom_table_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="圖片擷取工具必須綁定自訂表格",
            )
        ct = (
            db.query(CustomTable)
            .filter(CustomTable.id == payload.custom_table_id)
            .first()
        )
        if ct is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的自訂資料表不存在",
            )

    elif tool_type == "web_scraper":
        if not payload.target_url or not payload.target_url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="目標網址為必填"
            )
        if not payload.extract_description or not payload.extract_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="擷取描述為必填"
            )

    # Update common fields
    tool.name = payload.name
    tool.description = payload.description

    if tool_type == "external_api":
        tool.endpoint_url = payload.endpoint_url
        tool.http_method = payload.http_method
        tool.auth_type = payload.auth_type or "none"
        tool.auth_header_name = payload.auth_header_name

        if payload.credential and payload.credential.strip():
            tool.credential_enc = _encrypt(payload.credential)
        # else: keep existing credential_enc

        # Replace body params
        db.query(ToolBodyParam).filter(ToolBodyParam.tool_id == tool_id).delete()
        for idx, param in enumerate(payload.body_params or []):
            db.add(
                ToolBodyParam(
                    tool_id=tool.id,
                    param_name=param.param_name,
                    param_type=param.param_type,
                    is_required=param.is_required,
                    description=param.description,
                    sort_order=idx,
                )
            )

    elif tool_type == "image_extract":
        # Update custom_table_id
        tool.custom_table_id = payload.custom_table_id

    elif tool_type == "web_scraper":
        # Replace web scraper configs
        db.query(ToolWebScraperConfig).filter(
            ToolWebScraperConfig.tool_id == tool_id
        ).delete()
        db.add(
            ToolWebScraperConfig(
                tool_id=tool.id,
                target_url=payload.target_url,
                extract_description=payload.extract_description,
                max_chars=payload.max_chars if payload.max_chars is not None else 4000,
            )
        )

    db.commit()
    system_logger.info(f"User {auth.user_id} updated tool {tool.id} ({tool.name})")
    return {"message": "更新成功"}


# ---------------------------------------------------------------------------
# DELETE /tool/{id}
# ---------------------------------------------------------------------------


@router.delete("/{tool_id}", status_code=status.HTTP_200_OK)
def delete_tool(
    tool_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Delete a tool and all related body params. Requires fn_tool permission."""
    if not _has_fn_tool_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工具不存在")

    db.query(ToolBodyParam).filter(ToolBodyParam.tool_id == tool_id).delete()
    db.query(ToolWebScraperConfig).filter(
        ToolWebScraperConfig.tool_id == tool_id
    ).delete()
    db.delete(tool)
    db.commit()
    system_logger.info(f"User {auth.user_id} deleted tool {tool_id}")
    return {"message": "刪除成功"}


# ---------------------------------------------------------------------------
# POST /tool/test
# ---------------------------------------------------------------------------


@router.post("/test", status_code=status.HTTP_200_OK)
def test_tool(
    payload: ToolTestRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Test external API connectivity. Requires fn_tool permission."""
    if not _has_fn_tool_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not payload.endpoint_url or not payload.endpoint_url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="API Endpoint URL 為必填"
        )
    if payload.http_method not in VALID_HTTP_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP Method 不合法"
        )

    # Resolve credential
    credential: str | None = None
    if payload.tool_id is not None:
        tool = db.query(Tool).filter(Tool.id == payload.tool_id).first()
        if tool and tool.credential_enc:
            credential = _decrypt(tool.credential_enc)
    else:
        credential = payload.credential

    # Build headers
    headers: dict[str, str] = {}
    if payload.auth_type == "api_key" and payload.auth_header_name and credential:
        headers[payload.auth_header_name] = credential
    elif payload.auth_type == "bearer" and credential:
        headers["Authorization"] = f"Bearer {credential}"

    # Build body
    json_body = (
        payload.body_params_values if payload.http_method in {"POST", "PUT"} else None
    )

    # Execute request
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.request(
                method=payload.http_method,
                url=payload.endpoint_url,
                headers=headers,
                json=json_body,
            )
        # Try to parse response as JSON, fall back to text
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        result = ToolTestResult(
            http_status=response.status_code, response_body=response_body
        )
        return {"message": "測試完成", "data": result.model_dump()}

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"外部 API 連線失敗：{exc}",
        ) from exc
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"外部 API 連線失敗：{exc}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"外部 API 連線失敗：{exc}",
        ) from exc
