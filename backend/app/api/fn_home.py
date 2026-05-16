"""/api/home router — 首頁夥伴/資料表清單與最愛切換 (fn_home)."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schema.fn_home import (
    FavoriteToggleData,
    FavoriteToggleOut,
    FavoriteToggleRequest,
    HomePartnerItem,
    HomePartnersOut,
    HomeTableItem,
    HomeTablesOut,
)
from app.db.connector import get_db
from app.db.models.fn_ai_partner_chat import RoleAiPartner
from app.db.models.fn_ai_partner_config import AiPartnerConfig
from app.db.models.fn_custom_table import CustomTable, RoleCustomTable
from app.db.models.fn_home import UserFavorite
from app.db.models.user_role import UserRole
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/home", tags=["fn_home"])

ITEM_TYPE_PARTNER = "partner"
ITEM_TYPE_TABLE = "table"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_role_ids(user_id: int, db: Session) -> list[int]:
    rows = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    return [r.role_id for r in rows]


def _get_available_partner_ids(user_id: int, db: Session) -> set[int]:
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


def _get_authorized_table_ids(user_id: int, db: Session) -> set[int]:
    role_ids = _get_role_ids(user_id, db)
    if not role_ids:
        return set()
    rows = db.query(RoleCustomTable).filter(RoleCustomTable.role_id.in_(role_ids)).all()
    return {r.table_id for r in rows}


def _next_sort_order(user_id: int, db: Session) -> int:
    """Return max sort_order + 1 for the user's favorites."""
    result = (
        db.query(func.max(UserFavorite.sort_order))
        .filter(UserFavorite.user_id == user_id)
        .scalar()
    )
    return (result or 0) + 1


# ── GET /api/home/partners ────────────────────────────────────────────────────


@router.get("/partners", response_model=HomePartnersOut)
def list_home_partners(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> HomePartnersOut:
    """取得首頁夥伴清單，含 is_favorite 與 sort_order 欄位。"""
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

    favorite_rows = (
        db.query(UserFavorite)
        .filter(
            UserFavorite.user_id == auth.user_id,
            UserFavorite.item_type == ITEM_TYPE_PARTNER,
        )
        .all()
    )
    favorite_map: dict[int, int] = {r.item_id: r.sort_order for r in favorite_rows}

    items = [
        HomePartnerItem(
            id=p.id,
            name=p.name,
            description=p.description,
            is_favorite=(p.id in favorite_map),
            sort_order=favorite_map.get(p.id, 0),
        )
        for p in partners
    ]
    return HomePartnersOut(data=items)


# ── GET /api/home/tables ──────────────────────────────────────────────────────


@router.get("/tables", response_model=HomeTablesOut)
def list_home_tables(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> HomeTablesOut:
    """取得首頁授權資料表清單，含 is_favorite 與 sort_order 欄位。"""
    authorized_ids = _get_authorized_table_ids(auth.user_id, db)
    if not authorized_ids:
        return HomeTablesOut(data=[])

    tables = db.query(CustomTable).filter(CustomTable.id.in_(authorized_ids)).all()

    favorite_rows = (
        db.query(UserFavorite)
        .filter(
            UserFavorite.user_id == auth.user_id,
            UserFavorite.item_type == ITEM_TYPE_TABLE,
        )
        .all()
    )
    favorite_map: dict[int, int] = {r.item_id: r.sort_order for r in favorite_rows}

    items = [
        HomeTableItem(
            id=t.id,
            name=t.name,
            description=t.description,
            is_favorite=(t.id in favorite_map),
            sort_order=favorite_map.get(t.id, 0),
        )
        for t in tables
    ]
    return HomeTablesOut(data=items)


# ── POST /api/home/favorite/toggle ───────────────────────────────────────────


@router.post("/favorite/toggle", response_model=FavoriteToggleOut)
def toggle_favorite(
    payload: FavoriteToggleRequest,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> FavoriteToggleOut:
    """切換最愛狀態（夥伴或資料表）。"""
    if payload.item_type not in (ITEM_TYPE_PARTNER, ITEM_TYPE_TABLE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="item_type 必須為 'partner' 或 'table'",
        )

    # 驗證存取權限
    if payload.item_type == ITEM_TYPE_PARTNER:
        available_ids = _get_available_partner_ids(auth.user_id, db)
    else:
        available_ids = _get_authorized_table_ids(auth.user_id, db)

    if payload.item_id not in available_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    existing = (
        db.query(UserFavorite)
        .filter(
            UserFavorite.user_id == auth.user_id,
            UserFavorite.item_type == payload.item_type,
            UserFavorite.item_id == payload.item_id,
        )
        .first()
    )

    if existing is None:
        new_favorite = UserFavorite(
            user_id=auth.user_id,
            item_type=payload.item_type,
            item_id=payload.item_id,
            sort_order=_next_sort_order(auth.user_id, db),
        )
        db.add(new_favorite)
        db.commit()
        response.status_code = status.HTTP_201_CREATED
        return FavoriteToggleOut(
            message="已加入最愛",
            data=FavoriteToggleData(
                item_type=payload.item_type,
                item_id=payload.item_id,
                is_favorite=True,
            ),
        )
    else:
        db.delete(existing)
        db.commit()
        return FavoriteToggleOut(
            message="已取消最愛",
            data=FavoriteToggleData(
                item_type=payload.item_type,
                item_id=payload.item_id,
                is_favorite=False,
            ),
        )
