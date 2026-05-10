from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.models.base import Base


class BinanceRecentTrade(Base):
    """Recent individual trades per symbol (up to 500 latest per fetch)."""

    __tablename__ = "binance_recent_trades"
    __table_args__ = (
        UniqueConstraint("symbol", "trade_id", name="uq_binance_recent_trades_symbol_trade"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    trade_id = Column(BigInteger, nullable=False, index=True)
    price = Column(Numeric(30, 10), nullable=False)
    qty = Column(Numeric(30, 10), nullable=False)
    quote_qty = Column(Numeric(30, 10))
    trade_time = Column(DateTime(timezone=True), nullable=False, index=True)
    is_buyer_maker = Column(Boolean)