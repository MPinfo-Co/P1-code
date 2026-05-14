"""/expert/analysis router — 資安專家一鍵分析觸發與狀態查詢 (fn_expert)。

TDD #1: POST /expert/analysis/trigger
TDD #2: GET  /expert/analysis/status
"""

from __future__ import annotations

from datetime import datetime, timezone

from apscheduler.triggers.date import DateTrigger
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.connector import get_db
from app.db.models.analysis import DailyAnalysis, LogBatch
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import UserRole
from app.logger_utils.log_channels import get_system_logger
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/expert", tags=["fn_expert"])
logger = get_system_logger()

FN_EXPERT_CODE = "fn_expert"
SETTING_ID = 1


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------


def _has_fn_expert_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_expert function permission."""
    fn = (
        db.query(FunctionItems)
        .filter(FunctionItems.function_code == FN_EXPERT_CODE)
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
# Request schemas
# ---------------------------------------------------------------------------


class TriggerRequest(BaseModel):
    time_from: datetime
    time_to: datetime


# ---------------------------------------------------------------------------
# POST /expert/log/trigger
# ---------------------------------------------------------------------------


@router.post("/log/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_log_fetch(
    body: TriggerRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """手動觸發 Haiku 拉 SSB log。"""
    if not _has_fn_expert_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    running = db.query(LogBatch).filter(LogBatch.status == "running").first()
    if running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="抓 log 進行中，請稍後再試",
        )

    batch = LogBatch(
        time_from=body.time_from,
        time_to=body.time_to,
        status="running",
        records_fetched=0,
        chunks_total=0,
        chunks_done=0,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    _dispatch_haiku_job(
        time_from=body.time_from, time_to=body.time_to, batch_id=batch.id
    )

    logger.info(f"trigger_log_fetch: user={auth.user_id} batch={batch.id}")
    return {"message": "已啟動抓 log"}


# ---------------------------------------------------------------------------
# POST /expert/analysis/trigger
# ---------------------------------------------------------------------------


@router.post("/analysis/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_analysis(
    body: TriggerRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """手動觸發 Sonnet 彙整指定時段內的 chunk_results。

    不再讀 is_enabled 分歧、不再順帶觸發 Haiku，純粹只跑 Sonnet。
    """
    if not _has_fn_expert_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # 409: Sonnet 進行中（不看 LogBatch；Haiku 不擋 Sonnet，互鎖規則）
    processing = (
        db.query(DailyAnalysis).filter(DailyAnalysis.status == "processing").first()
    )
    if processing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="彙整進行中，請稍後再試",
        )

    # 同步寫 processing 標記，UPSERT 當日紀錄
    now = datetime.now(timezone.utc)
    today = now.date()
    da = db.query(DailyAnalysis).filter(DailyAnalysis.analysis_date == today).first()
    if da is None:
        da = DailyAnalysis(analysis_date=today, status="processing", started_at=now)
        db.add(da)
    else:
        da.status = "processing"
        da.started_at = now
    db.commit()

    _dispatch_sonnet_job(time_from=body.time_from, time_to=body.time_to)

    logger.info(
        f"trigger_analysis: user={auth.user_id} from={body.time_from} to={body.time_to}"
    )
    return {"message": "分析已啟動"}


# ---------------------------------------------------------------------------
# GET /expert/analysis/status
# ---------------------------------------------------------------------------


@router.get("/analysis/status", status_code=status.HTTP_200_OK)
def get_analysis_status(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """查詢分析狀態。

    回傳 idle / running / success / failed 之一，附 events_created 或 error_message。
    """
    if not _has_fn_expert_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # 優先判斷是否有進行中任務
    running_batch = db.query(LogBatch).filter(LogBatch.status == "running").first()
    processing_daily = (
        db.query(DailyAnalysis).filter(DailyAnalysis.status == "processing").first()
    )
    if running_batch or processing_daily:
        return {
            "message": "ok",
            "data": {
                "status": "running",
                "events_created": None,
                "error_message": None,
            },
        }

    # 查詢 tb_daily_analysis 最近一筆
    latest = (
        db.query(DailyAnalysis).order_by(DailyAnalysis.analysis_date.desc()).first()
    )
    if latest is None:
        return {
            "message": "ok",
            "data": {
                "status": "idle",
                "events_created": None,
                "error_message": None,
            },
        }

    if latest.status == "done":
        return {
            "message": "ok",
            "data": {
                "status": "success",
                "events_created": latest.events_created,
                "error_message": None,
            },
        }

    if latest.status == "failed":
        return {
            "message": "ok",
            "data": {
                "status": "failed",
                "events_created": None,
                "error_message": latest.error_message,
            },
        }

    # pending 或其他狀態 → idle
    return {
        "message": "ok",
        "data": {
            "status": "idle",
            "events_created": None,
            "error_message": None,
        },
    }


# ---------------------------------------------------------------------------
# One-shot job dispatchers
# ---------------------------------------------------------------------------


def _run_sonnet_manual() -> None:
    """直接執行 Sonnet 任務（manual_mode=True，繞過 is_enabled 守門）。

    手動觸發 pipeline 必須走這個入口，不可走 scheduler._sonnet_job —— 後者
    沒有 manual_mode 通道，會在 is_enabled=False 時早退讓 Sonnet 整段被跳過。
    包 try/except 防單次失敗炸掉背景 thread。
    """
    from anthropic import Anthropic

    from app.config.settings import settings as _settings
    from app.db.connector import SessionLocal
    from app.tasks.pro_task import run_pro_task

    try:
        run_pro_task(
            anthropic_client_factory=lambda: Anthropic(
                api_key=_settings.anthropic_api_key
            ),
            db_factory=SessionLocal,
            manual_mode=True,
        )
    except Exception:
        logger.exception("manual sonnet run failed")


def _dispatch_sonnet_job(time_from: datetime, time_to: datetime) -> None:
    """投遞一次性 Sonnet 任務。

    接受 time_from/time_to 但暫時不 forward 給 _run_sonnet_manual（P4-T9 補上）。
    """
    from app import scheduler as _scheduler_mod

    sched = _scheduler_mod._scheduler
    if sched is not None and sched.running:
        sched.add_job(
            _run_sonnet_manual,
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            id=f"manual_sonnet_{datetime.now(timezone.utc).timestamp()}",
            replace_existing=False,
            misfire_grace_time=300,
        )
    else:
        import threading

        t = threading.Thread(target=_run_sonnet_manual, daemon=True)
        t.start()


def _dispatch_haiku_job(
    time_from: datetime,
    time_to: datetime,
    batch_id: int,
) -> None:
    """投遞一次性 Haiku 任務，完成後串接 Sonnet（is_enabled=False 路徑）。

    pipeline 由 haiku_task 使用傳入的 time_from/time_to，
    batch row 已在 trigger API 中同步建立。
    """
    from app import scheduler as _scheduler_mod

    def _haiku_then_sonnet() -> None:
        from anthropic import Anthropic

        from app.db.connector import SessionLocal
        from app.tasks.haiku_task import run_haiku_task
        from app.tasks.ssb_client import SSBClient

        run_haiku_task(
            ssb_client_factory=lambda **kw: SSBClient(**kw),
            anthropic_client_factory=lambda **kw: Anthropic(**kw),
            db_factory=SessionLocal,
            time_from=time_from,
            time_to=time_to,
            batch_id=batch_id,
        )
        _run_sonnet_manual()

    sched = _scheduler_mod._scheduler
    if sched is not None and sched.running:
        sched.add_job(
            _haiku_then_sonnet,
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            id=f"manual_haiku_{datetime.now(timezone.utc).timestamp()}",
            replace_existing=False,
            misfire_grace_time=300,
        )
    else:
        import threading

        t = threading.Thread(target=_haiku_then_sonnet, daemon=True)
        t.start()
