from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.scheduler_log import BinanceSchedulerLog
from app.utils.logger import get_logger

logger = get_logger(__name__)


def log_job(
    session: Session,
    job_name: str,
    status: str,
    records_processed: int = 0,
    duration_seconds: float | None = None,
    error_message: str | None = None,
    started_at: datetime | None = None,
) -> None:
    entry = BinanceSchedulerLog(
        job_name=job_name,
        status=status,
        records_processed=records_processed,
        duration_seconds=duration_seconds,
        error_message=error_message,
        started_at=started_at or datetime.now(tz=timezone.utc),
        finished_at=datetime.now(tz=timezone.utc),
    )
    session.add(entry)