from datetime import datetime

from pydantic import BaseModel


class IngestPayload(BaseModel):
    time_from: datetime
    time_to: datetime
    records_fetched: int
    analysis_mode: str = "full"
    logs: list[dict]
