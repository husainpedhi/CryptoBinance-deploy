from sqlalchemy import Boolean, Column, Integer, Numeric, String, UniqueConstraint

from app.models.base import Base, TimestampMixin


class BinanceTradingPair(Base, TimestampMixin):
    """All trading pairs available on Binance (refreshed hourly)."""

    __tablename__ = "binance_trading_pairs"
    __table_args__ = (UniqueConstraint("symbol", name="uq_binance_trading_pairs_symbol"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    base_asset = Column(String(20), nullable=False)
    quote_asset = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="TRADING")
    is_active = Column(Boolean, nullable=False, default=True)
    min_price = Column(Numeric(30, 10))
    max_price = Column(Numeric(30, 10))
    tick_size = Column(Numeric(30, 10))
    min_qty = Column(Numeric(30, 10))
    max_qty = Column(Numeric(30, 10))
    step_size = Column(Numeric(30, 10))