"""/api/skill router — skill management (fn_skill)."""

import base64
import os

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.schema.fn_skill import (
    SkillCreate,
    SkillItem,
    SkillTestRequest,
    SkillTestResult,
    SkillUpdate,
)
from app.config.settings import settings
from app.db.connector import get_db
from app.db.models.fn_skill import Skill, SkillBodyParam
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import UserRole
from app.logger_utils import get_system_logger
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/api/skill", tags=["fn_skill"])
system_logger = get_system_logger()

FN_SKILL_NAME = "fn_skill"

VALID_AUTH_TYPES = {"none", "api_key", "bearer"}
VALID_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE"}


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------


def _has_fn_skill_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_skill function permission."""
    fn = db.query(FunctionItems).filter(FunctionItems.function_code == FN_SKILL_NAME).first()
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
# GET /api/skill
# ---------------------------------------------------------------------------


@router.get("", status_code=status.HTTP_200_OK)
def list_skills(
    keyword: str | None = Query(None, description="技能名稱關鍵字篩選（ILIKE）"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """List skills, optionally filtered by keyword. Requires fn_skill permission."""
    if not _has_fn_skill_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    query = db.query(Skill)
    if keyword:
        query = query.filter(Skill.name.ilike(f"%{keyword}%"))
    skills = query.order_by(Skill.created_at.asc()).all()

    items = [
        SkillItem(
            id=s.id,
            name=s.name,
            description=s.description,
            endpoint_url=s.endpoint_url,
            http_method=s.http_method,
            auth_type=s.auth_type,
            auth_header_name=s.auth_header_name,
            has_credential=s.credential_enc is not None,
        )
        for s in skills
    ]
    return {"message": "查詢成功", "data": [i.model_dump() for i in items]}


# ---------------------------------------------------------------------------
# POST /api/skill
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
def add_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Create a new skill. Requires fn_skill permission."""
    if not _has_fn_skill_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # Validation
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能名稱為必填")
    if len(payload.name) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能名稱不可超過 100 字")
    if db.query(Skill).filter(Skill.name == payload.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能名稱已存在")
    if not payload.endpoint_url or not payload.endpoint_url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API Endpoint URL 為必填")
    if payload.auth_type not in VALID_AUTH_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="認證方式不合法")
    if payload.auth_type == "api_key" and (not payload.auth_header_name or not payload.auth_header_name.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API Key 模式下 Header 名稱為必填")
    if payload.auth_type in {"api_key", "bearer"} and (not payload.credential or not payload.credential.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="憑證為必填")
    if payload.http_method not in VALID_HTTP_METHODS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP Method 不合法")

    # Create skill
    credential_enc = _encrypt(payload.credential) if payload.credential else None
    skill = Skill(
        name=payload.name,
        description=payload.description,
        endpoint_url=payload.endpoint_url,
        http_method=payload.http_method,
        auth_type=payload.auth_type,
        auth_header_name=payload.auth_header_name,
        credential_enc=credential_enc,
    )
    db.add(skill)
    db.flush()

    for idx, param in enumerate(payload.body_params or []):
        db.add(
            SkillBodyParam(
                skill_id=skill.id,
                param_name=param.param_name,
                param_type=param.param_type,
                is_required=param.is_required,
                description=param.description,
                sort_order=idx,
            )
        )

    db.commit()
    system_logger.info(f"User {auth.user_id} created skill {skill.id} ({skill.name})")
    return {"message": "新增成功"}


# ---------------------------------------------------------------------------
# PATCH /api/skill/{id}
# ---------------------------------------------------------------------------


@router.patch("/{skill_id}", status_code=status.HTTP_200_OK)
def update_skill(
    skill_id: int,
    payload: SkillUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Update a skill. Requires fn_skill permission."""
    if not _has_fn_skill_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")

    # Validation
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能名稱為必填")
    if len(payload.name) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能名稱不可超過 100 字")
    conflict = db.query(Skill).filter(Skill.name == payload.name, Skill.id != skill_id).first()
    if conflict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="技能名稱已存在")
    if not payload.endpoint_url or not payload.endpoint_url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API Endpoint URL 為必填")
    if payload.auth_type not in VALID_AUTH_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="認證方式不合法")
    if payload.auth_type == "api_key" and (not payload.auth_header_name or not payload.auth_header_name.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API Key 模式下 Header 名稱為必填")
    if payload.http_method not in VALID_HTTP_METHODS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP Method 不合法")

    # Update fields
    skill.name = payload.name
    skill.description = payload.description
    skill.endpoint_url = payload.endpoint_url
    skill.http_method = payload.http_method
    skill.auth_type = payload.auth_type
    skill.auth_header_name = payload.auth_header_name

    if payload.credential and payload.credential.strip():
        skill.credential_enc = _encrypt(payload.credential)
    # else: keep existing credential_enc

    # Replace body params
    db.query(SkillBodyParam).filter(SkillBodyParam.skill_id == skill_id).delete()
    for idx, param in enumerate(payload.body_params or []):
        db.add(
            SkillBodyParam(
                skill_id=skill.id,
                param_name=param.param_name,
                param_type=param.param_type,
                is_required=param.is_required,
                description=param.description,
                sort_order=idx,
            )
        )

    db.commit()
    system_logger.info(f"User {auth.user_id} updated skill {skill.id} ({skill.name})")
    return {"message": "更新成功"}


# ---------------------------------------------------------------------------
# DELETE /api/skill/{id}
# ---------------------------------------------------------------------------


@router.delete("/{skill_id}", status_code=status.HTTP_200_OK)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Delete a skill and all related body params. Requires fn_skill permission."""
    if not _has_fn_skill_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")

    db.query(SkillBodyParam).filter(SkillBodyParam.skill_id == skill_id).delete()
    db.delete(skill)
    db.commit()
    system_logger.info(f"User {auth.user_id} deleted skill {skill_id}")
    return {"message": "刪除成功"}


# ---------------------------------------------------------------------------
# POST /api/skill/test
# ---------------------------------------------------------------------------


@router.post("/test", status_code=status.HTTP_200_OK)
def test_skill(
    payload: SkillTestRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Test external API connectivity. Requires fn_skill permission."""
    if not _has_fn_skill_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not payload.endpoint_url or not payload.endpoint_url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API Endpoint URL 為必填")
    if payload.http_method not in VALID_HTTP_METHODS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP Method 不合法")

    # Resolve credential
    credential: str | None = None
    if payload.skill_id is not None:
        skill = db.query(Skill).filter(Skill.id == payload.skill_id).first()
        if skill and skill.credential_enc:
            credential = _decrypt(skill.credential_enc)
    else:
        credential = payload.credential

    # Build headers
    headers: dict[str, str] = {}
    if payload.auth_type == "api_key" and payload.auth_header_name and credential:
        headers[payload.auth_header_name] = credential
    elif payload.auth_type == "bearer" and credential:
        headers["Authorization"] = f"Bearer {credential}"

    # Build body
    json_body = payload.body_params_values if payload.http_method in {"POST", "PUT"} else None

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

        result = SkillTestResult(http_status=response.status_code, response_body=response_body)
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
