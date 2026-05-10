from sqlalchemy import Column, DateTime, Integer, Numeric, String, func

from app.models.base import Base


class BinanceOrderBookDepth(Base):
    """Full order book depth snapshot — configurable number of bid/ask levels."""

    __tablename__ = "binance_order_book_depth"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(3), nullable=False)      # BID or ASK
    level = Column(Integer, nullable=False)        # 1 = best, 2 = second best, ...
    price = Column(Numeric(30, 10), nullable=False)
    qty = Column(Numeric(30, 10), nullable=False)
    last_update_id = Column(Integer)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)