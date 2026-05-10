from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.models.base import Base


class BinanceAggTrade(Base):
    """Compressed aggregate trades — multiple fills rolled into one record."""

    __tablename__ = "binance_agg_trades"
    __table_args__ = (
        UniqueConstraint("symbol", "agg_trade_id", name="uq_binance_agg_trades_symbol_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    agg_trade_id = Column(BigInteger, nullable=False, index=True)
    price = Column(Numeric(30, 10), nullable=False)
    qty = Column(Numeric(30, 10), nullable=False)
    first_trade_id = Column(BigInteger)
    last_trade_id = Column(BigInteger)
    trade_time = Column(DateTime(timezone=True), nullable=False, index=True)
    is_buyer_maker = Column(Boolean)