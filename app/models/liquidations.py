from sqlalchemy import Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.models.base import Base


class BinanceLiquidation(Base):
    """Futures forced liquidation orders — large liquidations signal reversal risk."""

    __tablename__ = "binance_liquidations"
    __table_args__ = (
        UniqueConstraint("symbol", "trade_time", "price", "orig_qty", name="uq_binance_liquidation_symbol_time_price_qty"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(5), nullable=False)           # BUY or SELL
    order_type = Column(String(20))
    time_in_force = Column(String(10))
    orig_qty = Column(Numeric(30, 10))
    price = Column(Numeric(30, 10))
    avg_price = Column(Numeric(30, 10))
    order_status = Column(String(20))
    last_filled_qty = Column(Numeric(30, 10))
    accumulated_qty = Column(Numeric(30, 10))
    trade_time = Column(DateTime(timezone=True), nullable=False, index=True)