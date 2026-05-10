from sqlalchemy import Column, DateTime, Integer, Numeric, String, func

from app.models.base import Base


class BinanceTicker(Base):
    """Real-time 24-hour ticker snapshot per symbol (upserted every minute)."""

    __tablename__ = "binance_tickers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    price_change = Column(Numeric(30, 10))
    price_change_percent = Column(Numeric(10, 4))
    weighted_avg_price = Column(Numeric(30, 10))
    prev_close_price = Column(Numeric(30, 10))
    last_price = Column(Numeric(30, 10), nullable=False)
    bid_price = Column(Numeric(30, 10))
    ask_price = Column(Numeric(30, 10))
    open_price = Column(Numeric(30, 10))
    high_price = Column(Numeric(30, 10))
    low_price = Column(Numeric(30, 10))
    volume = Column(Numeric(30, 10))
    quote_volume = Column(Numeric(30, 10))
    open_time = Column(DateTime(timezone=True))
    close_time = Column(DateTime(timezone=True))
    trade_count = Column(Integer)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)