from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.models.base import Base


class BinanceSchedulerLog(Base):
    """Audit log for every scheduler job run."""

    __tablename__ = "binance_scheduler_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # success | error | skipped
    records_processed = Column(Integer, default=0)
    duration_seconds = Column(Float)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    finished_at = Column(DateTime(timezone=True))