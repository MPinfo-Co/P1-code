"""/api/home router — 首頁夥伴清單與最愛切換 (fn_home)."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.schema.fn_home import (
    FavoriteToggleData,
    FavoriteToggleOut,
    FavoriteToggleRequest,
    HomePartnerItem,
    HomePartnersOut,
)
from app.db.connector import get_db
from app.db.models.fn_ai_partner_chat import RoleAiPartner
from app.db.models.fn_ai_partner_config import AiPartnerConfig
from app.db.models.fn_home import UserFavoritePartner
from app.db.models.user_role import UserRole
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/home", tags=["fn_home"])


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_role_ids(user_id: int, db: Session) -> list[int]:
    """Return list of role_ids for the user."""
    rows = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    return [r.role_id for r in rows]


def _get_available_partner_ids(user_id: int, db: Session) -> set[int]:
    """Return set of partner_ids available to the user via role bindings (enabled only)."""
    role_ids = _get_role_ids(user_id, db)
    if not role_ids:
        return set()
    rows = (
        db.query(RoleAiPartner.partner_id)
        .join(AiPartnerConfig, AiPartnerConfig.id == RoleAiPartner.partner_id)
        .filter(
            RoleAiPartner.role_id.in_(role_ids),
            AiPartnerConfig.is_enabled.is_(True),
        )
        .distinct()
        .all()
    )
    return {r.partner_id for r in rows}


# ── GET /api/home/partners ───────────────────────────────────────────────────


@router.get("/partners", response_model=HomePartnersOut)
def list_home_partners(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> HomePartnersOut:
    """取得首頁夥伴清單，含 is_favorite 欄位。"""
    available_ids = _get_available_partner_ids(auth.user_id, db)
    if not available_ids:
        return HomePartnersOut(data=[])

    partners = (
        db.query(AiPartnerConfig)
        .filter(
            AiPartnerConfig.id.in_(available_ids),
            AiPartnerConfig.is_enabled.is_(True),
        )
        .all()
    )

    # 取得當前使用者的最愛清單
    favorite_rows = (
        db.query(UserFavoritePartner)
        .filter(UserFavoritePartner.user_id == auth.user_id)
        .all()
    )
    favorite_ids = {r.partner_id for r in favorite_rows}

    items = [
        HomePartnerItem(
            id=p.id,
            name=p.name,
            description=p.description,
            is_favorite=(p.id in favorite_ids),
        )
        for p in partners
    ]
    return HomePartnersOut(data=items)


# ── POST /api/home/favorite/toggle ──────────────────────────────────────────


@router.post("/favorite/toggle", response_model=FavoriteToggleOut)
def toggle_favorite(
    payload: FavoriteToggleRequest,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> FavoriteToggleOut:
    """切換單一夥伴的最愛狀態。"""
    # 驗證夥伴可用性
    available_ids = _get_available_partner_ids(auth.user_id, db)
    if payload.partner_id not in available_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # 查詢當前最愛狀態
    existing = (
        db.query(UserFavoritePartner)
        .filter(
            UserFavoritePartner.user_id == auth.user_id,
            UserFavoritePartner.partner_id == payload.partner_id,
        )
        .first()
    )

    if existing is None:
        # 不存在 → 新增（is_favorite: false → true），回應 201
        new_favorite = UserFavoritePartner(
            user_id=auth.user_id,
            partner_id=payload.partner_id,
        )
        db.add(new_favorite)
        db.commit()
        response.status_code = status.HTTP_201_CREATED
        return FavoriteToggleOut(
            message="已加入最愛",
            data=FavoriteToggleData(
                partner_id=payload.partner_id,
                is_favorite=True,
            ),
        )
    else:
        # 已存在 → 刪除（is_favorite: true → false），回應 200
        db.delete(existing)
        db.commit()
        return FavoriteToggleOut(
            message="已取消最愛",
            data=FavoriteToggleData(
                partner_id=payload.partner_id,
                is_favorite=False,
            ),
        )
