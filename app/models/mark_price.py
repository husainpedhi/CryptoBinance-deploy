from sqlalchemy import Column, DateTime, Integer, Numeric, String, func

from app.models.base import Base


class BinanceMarkPrice(Base):
    """Futures mark price, index price and current funding rate (time-series snapshot)."""

    __tablename__ = "binance_mark_price"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    mark_price = Column(Numeric(30, 10), nullable=False)
    index_price = Column(Numeric(30, 10))
    estimated_settle_price = Column(Numeric(30, 10))
    last_funding_rate = Column(Numeric(20, 10))
    next_funding_time = Column(DateTime(timezone=True))
    interest_rate = Column(Numeric(20, 10))
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)