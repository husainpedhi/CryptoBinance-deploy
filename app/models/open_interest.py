from sqlalchemy import Column, DateTime, Integer, Numeric, String, func

from app.models.base import Base


class BinanceOpenInterest(Base):
    """Current open interest snapshot per futures symbol (time-series)."""

    __tablename__ = "binance_open_interest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    open_interest = Column(Numeric(30, 10), nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)