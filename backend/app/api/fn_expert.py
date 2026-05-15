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
from app.db.models.analysis import ChunkResult, DailyAnalysis, LogBatch
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


class LogTriggerRequest(BaseModel):
    time_from: datetime
    time_to: datetime
    force: bool = False


# ---------------------------------------------------------------------------
# POST /expert/log/trigger
# ---------------------------------------------------------------------------


@router.post("/log/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_log_fetch(
    body: LogTriggerRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """手動觸發 Haiku 拉 SSB log。

    重疊處理（A+D 策略）：
      - 與 running batch 重疊 → 409 overlap_type=running，不可繞過
      - 新範圍涵蓋舊範圍 → 自動刪舊建新（無資料遺失）
      - 部分重疊（錯位 / 新範圍在舊範圍內 / 蓋舊一半）→ 409 overlap_type=partial，
        附舊 batch 資訊；前端二次確認後帶 force=true 重送即可
    """
    if not _has_fn_expert_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # DB 端 LogBatch.time_from / time_to 都是 TIMESTAMP WITHOUT TIME ZONE（naive），
    # Pydantic 收到的 body 是 tz-aware；統一轉 naive UTC 才能與 DB 值直接比較。
    def _strip_tz(dt: datetime) -> datetime:
        return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt

    new_from = _strip_tz(body.time_from)
    new_to = _strip_tz(body.time_to)

    # 查所有時段重疊的 batch（PostgreSQL 標準區間重疊判定：
    # 新區間與舊區間有交集 ⇔ 新 from < 舊 to AND 新 to > 舊 from）
    overlapping = (
        db.query(LogBatch)
        .filter(
            LogBatch.time_from < new_to,
            LogBatch.time_to > new_from,
        )
        .all()
    )

    # 1) running 重疊 → 不可繞過
    if any(b.status == "running" for b in overlapping):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "抓 log 進行中，請稍後再試",
                "overlap_type": "running",
            },
        )

    # 2) 找「新範圍未涵蓋」的舊 batch（partial overlap）
    not_covered = [
        b for b in overlapping if not (new_from <= b.time_from and new_to >= b.time_to)
    ]
    if not_covered and not body.force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "此時段與既有抓取紀錄部分重疊，確認是否刪除舊紀錄重新抓取？",
                "overlap_type": "partial",
                "overlapping_batches": [
                    {
                        "id": b.id,
                        "time_from": b.time_from.isoformat(),
                        "time_to": b.time_to.isoformat(),
                    }
                    for b in not_covered
                ],
            },
        )

    # 3) 通過：刪所有重疊 batch（與其 chunks）；FK 無 CASCADE，手動先刪 chunks
    deleted_ids = [b.id for b in overlapping]
    for b in overlapping:
        db.query(ChunkResult).filter(ChunkResult.batch_id == b.id).delete()
        db.delete(b)
    if overlapping:
        db.commit()

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

    logger.info(
        f"trigger_log_fetch: user={auth.user_id} batch={batch.id} "
        f"deleted_overlapping={deleted_ids} force={body.force}"
    )
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
    """查詢 Haiku（拉 log）與 Sonnet（彙整）各自的狀態。"""
    if not _has_fn_expert_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    return {
        "message": "ok",
        "data": {
            "haiku": _resolve_haiku_status(db),
            "sonnet": _resolve_sonnet_status(db),
        },
    }


def _resolve_haiku_status(db: Session) -> dict:
    running = db.query(LogBatch).filter(LogBatch.status == "running").first()
    if running:
        return {"status": "running", "records_fetched": None, "error_message": None}

    # 用 id.desc()：使用者可能挑歷史時段手動抓取（time_to 是過去某時點），
    # id 是 auto-increment，保證取到「最後 trigger 的那筆」。
    latest = db.query(LogBatch).order_by(LogBatch.id.desc()).first()
    if latest is None:
        return {"status": "idle", "records_fetched": None, "error_message": None}

    if latest.status == "done":
        return {
            "status": "success",
            "records_fetched": latest.records_fetched,
            "error_message": None,
        }
    if latest.status == "failed":
        return {
            "status": "failed",
            "records_fetched": None,
            "error_message": latest.error_message,
        }
    return {"status": "idle", "records_fetched": None, "error_message": None}


def _resolve_sonnet_status(db: Session) -> dict:
    processing = (
        db.query(DailyAnalysis).filter(DailyAnalysis.status == "processing").first()
    )
    if processing:
        return {"status": "running", "events_created": None, "error_message": None}

    latest = (
        db.query(DailyAnalysis).order_by(DailyAnalysis.analysis_date.desc()).first()
    )
    if latest is None:
        return {"status": "idle", "events_created": None, "error_message": None}

    if latest.status == "done":
        return {
            "status": "success",
            "events_created": latest.events_created,
            "error_message": None,
        }
    if latest.status == "failed":
        return {
            "status": "failed",
            "events_created": None,
            "error_message": latest.error_message,
        }
    return {"status": "idle", "events_created": None, "error_message": None}


# ---------------------------------------------------------------------------
# One-shot job dispatchers
# ---------------------------------------------------------------------------


def _run_sonnet_manual(time_from: datetime, time_to: datetime) -> None:
    """直接執行 Sonnet 任務（manual_mode=True，繞過 sonnet_enabled 守門）。

    手動觸發 pipeline 必須走這個入口，不可走 scheduler._sonnet_job —— 後者
    沒有 manual_mode 通道，會在 sonnet_enabled=False 時早退讓 Sonnet 整段被跳過。
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
            time_from=time_from,
            time_to=time_to,
        )
    except Exception:
        logger.exception("manual sonnet run failed")


def _dispatch_sonnet_job(time_from: datetime, time_to: datetime) -> None:
    """投遞一次性 Sonnet 任務（is_enabled=True 路徑）。"""
    from app import scheduler as _scheduler_mod

    def _run() -> None:
        _run_sonnet_manual(time_from=time_from, time_to=time_to)

    sched = _scheduler_mod._scheduler
    if sched is not None and sched.running:
        sched.add_job(
            _run,
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            id=f"manual_sonnet_{datetime.now(timezone.utc).timestamp()}",
            replace_existing=False,
            misfire_grace_time=300,
        )
    else:
        import threading

        threading.Thread(target=_run, daemon=True).start()


def _dispatch_haiku_job(
    time_from: datetime,
    time_to: datetime,
    batch_id: int,
) -> None:
    """投遞一次性 Haiku 任務（解耦：不再串接 Sonnet）。

    pipeline 由 haiku_task 使用傳入的 time_from/time_to，
    batch row 已在 trigger API 中同步建立。
    """
    from app import scheduler as _scheduler_mod

    def _haiku() -> None:
        from anthropic import Anthropic

        from app.db.connector import SessionLocal
        from app.tasks.haiku_task import run_haiku_task
        from app.tasks.ssb_client import SSBClient

        try:
            run_haiku_task(
                ssb_client_factory=lambda **kw: SSBClient(**kw),
                anthropic_client_factory=lambda **kw: Anthropic(**kw),
                db_factory=SessionLocal,
                time_from=time_from,
                time_to=time_to,
                batch_id=batch_id,
            )
        except Exception:
            logger.exception("manual haiku run failed")

    sched = _scheduler_mod._scheduler
    if sched is not None and sched.running:
        sched.add_job(
            _haiku,
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            id=f"manual_haiku_{datetime.now(timezone.utc).timestamp()}",
            replace_existing=False,
            misfire_grace_time=300,
        )
    else:
        import threading

        threading.Thread(target=_haiku, daemon=True).start()
