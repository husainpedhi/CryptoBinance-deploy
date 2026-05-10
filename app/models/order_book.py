from sqlalchemy import Column, DateTime, Integer, Numeric, String, func

from app.models.base import Base


class BinanceOrderBook(Base):
    """Top-of-book bid/ask snapshot per symbol (sampled with tickers)."""

    __tablename__ = "binance_order_book"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    last_update_id = Column(Integer)
    bid_price = Column(Numeric(30, 10), nullable=False)
    bid_qty = Column(Numeric(30, 10), nullable=False)
    ask_price = Column(Numeric(30, 10), nullable=False)
    ask_qty = Column(Numeric(30, 10), nullable=False)
    spread = Column(Numeric(30, 10))
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)