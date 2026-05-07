"""/api/expert router — 資安專家設定 (fn_expert_setting)."""

import base64
import os
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schema.fn_expert_setting import (
    ExpertSettingOut,
    ExpertSettingSaveRequest,
    SsbTestRequest,
)
from app.config.settings import settings
from app.db.connector import get_db
from app.db.models.fn_expert_setting import AiPartner, ExpertSetting
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import UserRole
from app.logger_utils import get_system_logger
from app.utils.util_store import AuthContext, authenticate
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

router = APIRouter(prefix="/api/expert", tags=["fn_expert_setting"])
system_logger = get_system_logger()

FN_EXPERT_SETTING_NAME = "fn_expert_setting"
EXPERT_PARTNER_NAME = "資安專家"

VALID_FREQUENCIES = {"daily", "weekly", "manual"}
_SCHEDULE_TIME_RE = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")

_AES_KEY_BYTES = 32


# ---------------------------------------------------------------------------
# AES-256-GCM helpers (shared pattern with fn_tool)
# ---------------------------------------------------------------------------


def _derive_key() -> bytes:
    """Derive a 32-byte key from settings.aes_key."""
    raw = settings.aes_key.encode("utf-8")
    return (raw * (_AES_KEY_BYTES // len(raw) + 1))[:_AES_KEY_BYTES]


def _encrypt(plain: str) -> str:
    """AES-256-GCM encrypt; returns base64-encoded nonce+ciphertext."""
    key = _derive_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
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
# Permission helper
# ---------------------------------------------------------------------------


def _has_fn_expert_setting_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_expert_setting function permission."""
    fn = (
        db.query(FunctionItems)
        .filter(FunctionItems.function_code == FN_EXPERT_SETTING_NAME)
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
# GET /api/expert/settings
# ---------------------------------------------------------------------------


@router.get("/settings", status_code=status.HTTP_200_OK)
def get_expert_settings(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """取得資安專家設定。Requires fn_expert_setting permission."""
    if not _has_fn_expert_setting_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # Find the 資安專家 partner
    partner = db.query(AiPartner).filter(AiPartner.name == EXPERT_PARTNER_NAME).first()

    if partner is None:
        # Return defaults when partner not set up yet
        data = ExpertSettingOut(
            is_enabled=False,
            frequency="daily",
            schedule_time="02:00",
            weekday=None,
            ssb_host=None,
            ssb_port=443,
            ssb_logspace=None,
            ssb_username=None,
            ssb_password=None,
        )
        return {"message": "查詢成功", "data": data.model_dump()}

    setting = (
        db.query(ExpertSetting).filter(ExpertSetting.partner_id == partner.id).first()
    )

    if setting is None:
        # Return defaults
        data = ExpertSettingOut(
            is_enabled=False,
            frequency="daily",
            schedule_time="02:00",
            weekday=None,
            ssb_host=None,
            ssb_port=443,
            ssb_logspace=None,
            ssb_username=None,
            ssb_password=None,
        )
        return {"message": "查詢成功", "data": data.model_dump()}

    # Mask password
    ssb_password: str | None = None
    if setting.ssb_password_enc:
        ssb_password = "********"

    data = ExpertSettingOut(
        is_enabled=setting.is_enabled,
        frequency=setting.frequency,
        schedule_time=setting.schedule_time,
        weekday=setting.weekday,
        ssb_host=setting.ssb_host,
        ssb_port=setting.ssb_port,
        ssb_logspace=setting.ssb_logspace,
        ssb_username=setting.ssb_username,
        ssb_password=ssb_password,
    )
    return {"message": "查詢成功", "data": data.model_dump()}


# ---------------------------------------------------------------------------
# PUT /api/expert/settings
# ---------------------------------------------------------------------------


@router.put("/settings", status_code=status.HTTP_200_OK)
def save_expert_settings(
    payload: ExpertSettingSaveRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """儲存資安專家設定。Requires fn_expert_setting permission."""
    if not _has_fn_expert_setting_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # --- Validation ---
    if payload.frequency not in VALID_FREQUENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="觸發頻率值不合法",
        )

    if payload.frequency != "manual":
        if not payload.schedule_time or not payload.schedule_time.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="觸發時間為必填",
            )
        if not _SCHEDULE_TIME_RE.match(payload.schedule_time):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="觸發時間格式錯誤",
            )

    if payload.frequency == "weekly":
        if payload.weekday is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="每週頻率需指定星期幾",
            )
        if payload.weekday < 0 or payload.weekday > 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="星期幾值不合法",
            )

    if not payload.ssb_host or not payload.ssb_host.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host 為必填欄位",
        )

    if payload.ssb_port < 1 or payload.ssb_port > 65535:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Port 需介於 1–65535",
        )

    if not payload.ssb_logspace or not payload.ssb_logspace.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logspace 為必填欄位",
        )

    if not payload.ssb_username or not payload.ssb_username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username 為必填欄位",
        )

    # --- Upsert logic ---
    partner = db.query(AiPartner).filter(AiPartner.name == EXPERT_PARTNER_NAME).first()
    if partner is None:
        # Create a stub partner if not yet in DB
        partner = AiPartner(name=EXPERT_PARTNER_NAME, is_builtin=True)
        db.add(partner)
        db.flush()

    existing = (
        db.query(ExpertSetting).filter(ExpertSetting.partner_id == partner.id).first()
    )

    # Check first-time password requirement
    if existing is None and (
        not payload.ssb_password or not payload.ssb_password.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="首次儲存需提供 SSB 密碼",
        )

    # Encrypt password if provided
    password_enc: str | None = None
    if payload.ssb_password and payload.ssb_password.strip():
        password_enc = _encrypt(payload.ssb_password)

    if existing is not None:
        existing.is_enabled = payload.is_enabled
        existing.frequency = payload.frequency
        existing.schedule_time = payload.schedule_time
        existing.weekday = payload.weekday
        existing.ssb_host = payload.ssb_host
        existing.ssb_port = payload.ssb_port
        existing.ssb_logspace = payload.ssb_logspace
        existing.ssb_username = payload.ssb_username
        if password_enc is not None:
            existing.ssb_password_enc = password_enc
        # else: keep existing password
    else:
        new_setting = ExpertSetting(
            partner_id=partner.id,
            is_enabled=payload.is_enabled,
            frequency=payload.frequency,
            schedule_time=payload.schedule_time,
            weekday=payload.weekday,
            ssb_host=payload.ssb_host,
            ssb_port=payload.ssb_port,
            ssb_logspace=payload.ssb_logspace,
            ssb_username=payload.ssb_username,
            ssb_password_enc=password_enc,
        )
        db.add(new_setting)

    db.commit()
    system_logger.info(f"User {auth.user_id} saved expert settings")
    return {"message": "設定已儲存"}


# ---------------------------------------------------------------------------
# POST /api/expert/ssb-test
# ---------------------------------------------------------------------------


@router.post("/ssb-test", status_code=status.HTTP_200_OK)
def test_ssb_connection(
    payload: SsbTestRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """測試 SSB 連線。Requires fn_expert_setting permission."""
    if not _has_fn_expert_setting_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # --- Validation ---
    if not payload.host or not payload.host.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host 為必填欄位",
        )

    if payload.port < 1 or payload.port > 65535:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Port 需介於 1–65535",
        )

    if not payload.logspace or not payload.logspace.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logspace 為必填欄位",
        )

    if not payload.username or not payload.username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username 為必填欄位",
        )

    if not payload.password or not payload.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password 為必填欄位",
        )

    # --- Resolve password ---
    test_password = payload.password
    if payload.password == "**":
        partner = (
            db.query(AiPartner).filter(AiPartner.name == EXPERT_PARTNER_NAME).first()
        )
        if partner:
            setting = (
                db.query(ExpertSetting)
                .filter(ExpertSetting.partner_id == partner.id)
                .first()
            )
            if setting and setting.ssb_password_enc:
                test_password = _decrypt(setting.ssb_password_enc)

    # --- Connect to SSB ---
    url = f"https://{payload.host}:{payload.port}/api/5/"
    try:
        with httpx.Client(timeout=10.0, verify=False) as http_client:
            response = http_client.get(
                url,
                auth=(payload.username, test_password),
            )
        if response.is_success:
            return {"message": "連線成功"}
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"無法連線至 SSB：HTTP {response.status_code}",
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"無法連線至 SSB：{exc}",
        ) from exc
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"無法連線至 SSB：{exc}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"無法連線至 SSB：{exc}",
        ) from exc
