import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.log_batch import IngestPayload
from app.tasks.flash_task import _process_ingest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest")
def ingest_logs(
    payload: IngestPayload,
    x_ingest_key: str = Header(default=""),
    db: Session = Depends(get_db),
):
    if settings.INGEST_SECRET and x_ingest_key != settings.INGEST_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid ingest key"
        )

    logger.info(
        f"Ingest received: {payload.records_fetched} raw logs, "
        f"{len(payload.logs)} records after preaggregate, "
        f"mode={payload.analysis_mode}"
    )

    result = _process_ingest(db, payload)
    return result
