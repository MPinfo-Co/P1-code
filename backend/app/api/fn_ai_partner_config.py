"""/ai-partner-config router — AI 夥伴設定管理 (fn_ai_partner_config)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.schema.fn_ai_partner_config import (
    AiPartnerCreate,
    AiPartnerItem,
    AiPartnerUpdate,
)
from app.db.connector import get_db
from app.db.models.fn_ai_partner_config import AiPartner, AiPartnerTool
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import UserRole
from app.logger_utils import get_system_logger
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/ai-partner-config", tags=["fn_ai_partner_config"])
system_logger = get_system_logger()

FN_AI_PARTNER_CONFIG_NAME = "fn_ai_partner_config"


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------


def _has_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_ai_partner_config function permission."""
    fn = (
        db.query(FunctionItems)
        .filter(FunctionItems.function_code == FN_AI_PARTNER_CONFIG_NAME)
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
# GET /ai-partner-config
# ---------------------------------------------------------------------------


@router.get("", status_code=status.HTTP_200_OK)
def list_ai_partners(
    keyword: str | None = Query(None, description="夥伴名稱或描述關鍵字（ILIKE）"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """List AI partners, optionally filtered by keyword. Requires fn_ai_partner_config permission."""
    if not _has_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    query = db.query(AiPartner)
    if keyword:
        query = query.filter(
            AiPartner.name.ilike(f"%{keyword}%")
            | AiPartner.description.ilike(f"%{keyword}%")
        )
    partners = query.order_by(AiPartner.created_at.asc()).all()

    partner_ids = [p.id for p in partners]
    all_links = (
        db.query(AiPartnerTool).filter(AiPartnerTool.partner_id.in_(partner_ids)).all()
        if partner_ids
        else []
    )
    tools_by_partner: dict[int, list[int]] = {}
    for link in all_links:
        tools_by_partner.setdefault(link.partner_id, []).append(link.tool_id)

    items = [
        AiPartnerItem(
            id=p.id,
            name=p.name,
            description=p.description,
            is_enabled=p.is_enabled,
            role_definition=p.role_definition,
            behavior_limit=p.behavior_limit,
            tool_ids=tools_by_partner.get(p.id, []),
        )
        for p in partners
    ]
    return {"message": "查詢成功", "data": [i.model_dump() for i in items]}


# ---------------------------------------------------------------------------
# POST /ai-partner-config
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
def add_ai_partner(
    payload: AiPartnerCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Create a new AI partner. Requires fn_ai_partner_config permission."""
    if not _has_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="夥伴名稱為必填",
        )

    if db.query(AiPartner).filter(AiPartner.name == payload.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="夥伴名稱已存在",
        )

    partner = AiPartner(
        name=payload.name,
        description=payload.description,
        role_definition=payload.role_definition,
        behavior_limit=payload.behavior_limit,
        is_builtin=False,
        is_enabled=True,
    )
    db.add(partner)
    db.flush()

    for tool_id in payload.tool_ids or []:
        db.add(AiPartnerTool(partner_id=partner.id, tool_id=tool_id))

    db.commit()
    system_logger.info(
        f"User {auth.user_id} created AI partner {partner.id} ({partner.name})"
    )
    return {"message": "新增成功"}


# ---------------------------------------------------------------------------
# PATCH /ai-partner-config/{id}
# ---------------------------------------------------------------------------


@router.patch("/{partner_id}", status_code=status.HTTP_200_OK)
def update_ai_partner(
    partner_id: int,
    payload: AiPartnerUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Update an AI partner. Requires fn_ai_partner_config permission."""
    if not _has_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    partner = db.query(AiPartner).filter(AiPartner.id == partner_id).first()
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI 夥伴不存在",
        )

    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="夥伴名稱為必填",
        )

    conflict = (
        db.query(AiPartner)
        .filter(AiPartner.name == payload.name, AiPartner.id != partner_id)
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="夥伴名稱已存在",
        )

    partner.name = payload.name
    partner.description = payload.description
    partner.role_definition = payload.role_definition
    partner.behavior_limit = payload.behavior_limit
    if payload.is_enabled is not None:
        partner.is_enabled = payload.is_enabled

    # Replace tool associations
    db.query(AiPartnerTool).filter(AiPartnerTool.partner_id == partner_id).delete()
    for tool_id in payload.tool_ids or []:
        db.add(AiPartnerTool(partner_id=partner.id, tool_id=tool_id))

    db.commit()
    system_logger.info(
        f"User {auth.user_id} updated AI partner {partner.id} ({partner.name})"
    )
    return {"message": "更新成功"}


# ---------------------------------------------------------------------------
# DELETE /ai-partner-config/{id}
# ---------------------------------------------------------------------------


@router.delete("/{partner_id}", status_code=status.HTTP_200_OK)
def delete_ai_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Delete an AI partner. Requires fn_ai_partner_config permission."""
    if not _has_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    partner = db.query(AiPartner).filter(AiPartner.id == partner_id).first()
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI 夥伴不存在",
        )

    if partner.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="內建夥伴不可刪除",
        )

    db.query(AiPartnerTool).filter(AiPartnerTool.partner_id == partner_id).delete()
    db.delete(partner)
    db.commit()
    system_logger.info(f"User {auth.user_id} deleted AI partner {partner_id}")
    return {"message": "刪除成功"}
