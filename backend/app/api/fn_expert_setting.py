"""/api/expert router — 資安專家設定 (fn_expert_setting)。

ExpertSetting 採單例設計：tb_expert_settings 永遠只有 id=1 一筆紀錄，
由 migration seed 寫入；API 只做 GET / PUT，無 list / create / delete。
"""

import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schema.fn_expert_setting import (
    ExpertSettingOut,
    ExpertSettingSaveRequest,
    SsbTestRequest,
)
from app.db.connector import get_db
from app.db.models.fn_expert_setting import ExpertSetting
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import UserRole
from app.logger_utils import get_system_logger
from app.utils.crypto import decrypt as _decrypt, encrypt as _encrypt
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/expert", tags=["fn_expert_setting"])
system_logger = get_system_logger()

FN_EXPERT_SETTING_NAME = "fn_expert_setting"
SETTING_ID = 1  # singleton row id

_SCHEDULE_TIME_RE = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")

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


def _get_or_create_singleton(db: Session) -> ExpertSetting:
    """Return the singleton ExpertSetting row, creating it lazily if missing.

    Migration seeds row id=1, but this guard makes the API robust against
    accidental row deletion.
    """
    record = db.get(ExpertSetting, SETTING_ID)
    if record is None:
        record = ExpertSetting(id=SETTING_ID)
        db.add(record)
        db.flush()
    return record


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

    setting = _get_or_create_singleton(db)
    db.commit()  # persist the row if it was just created

    ssb_password: str | None = None
    if setting.ssb_password_enc:
        ssb_password = "********"

    data = ExpertSettingOut(
        haiku_enabled=setting.haiku_enabled,
        haiku_interval_minutes=setting.haiku_interval_minutes,
        sonnet_enabled=setting.sonnet_enabled,
        schedule_time=setting.schedule_time,
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
    if payload.sonnet_enabled and payload.schedule_time:
        if not _SCHEDULE_TIME_RE.match(payload.schedule_time):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="觸發時間格式錯誤",
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

    # --- Update singleton ---
    record = _get_or_create_singleton(db)

    # First-time password requirement: if no password stored yet, payload must provide one.
    if not record.ssb_password_enc and (
        not payload.ssb_password or not payload.ssb_password.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="首次儲存需提供 SSB 密碼",
        )

    record.haiku_enabled = payload.haiku_enabled
    record.haiku_interval_minutes = payload.haiku_interval_minutes
    record.sonnet_enabled = payload.sonnet_enabled
    record.schedule_time = payload.schedule_time
    record.ssb_host = payload.ssb_host
    record.ssb_port = payload.ssb_port
    record.ssb_logspace = payload.ssb_logspace
    record.ssb_username = payload.ssb_username
    if payload.ssb_password and payload.ssb_password.strip():
        record.ssb_password_enc = _encrypt(payload.ssb_password)
    # else: keep existing password

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
        record = db.get(ExpertSetting, SETTING_ID)
        if record and record.ssb_password_enc:
            test_password = _decrypt(record.ssb_password_enc)

    # --- Connect to SSB ---
    # 兩步驗證:
    # 1. POST /api/5/login 拿 session token (驗證帳密)
    # 2. GET /api/5/search/logspace/list_logspaces 帶 cookie (驗證 logspace 存在)
    base_url = f"{payload.host}:{payload.port}"
    try:
        with httpx.Client(timeout=10.0, verify=False) as http_client:
            # Step 1: login
            login_resp = http_client.post(
                f"{base_url}/api/5/login",
                data={"username": payload.username, "password": test_password},
            )
            if not login_resp.is_success:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"無法連線至 SSB：HTTP {login_resp.status_code}",
                )
            login_body = login_resp.json()
            login_error = login_body.get("error") or {}
            if login_error.get("code") is not None:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"SSB 認證失敗：{login_error.get('message', '未知錯誤')}",
                )
            token = login_body.get("result")
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="SSB 回應格式異常：無 session token",
                )

            # Step 2: 驗證 logspace 存在
            list_resp = http_client.get(
                f"{base_url}/api/5/search/logspace/list_logspaces",
                headers={"Cookie": f"AUTHENTICATION_TOKEN={token}"},
            )
            if not list_resp.is_success:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"取得 logspace 清單失敗：HTTP {list_resp.status_code}",
                )
            logspaces = list_resp.json().get("result") or []
            if payload.logspace not in logspaces:
                available = ", ".join(logspaces) if logspaces else "(無)"
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Logspace「{payload.logspace}」不存在，可用：{available}",
                )

        return {"message": "連線成功"}
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
