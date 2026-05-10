from sqlalchemy import Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.models.base import Base


class BinanceTakerVolume(Base):
    """Taker buy vs sell volume for futures — shows who is the aggressor."""

    __tablename__ = "binance_taker_volume"
    __table_args__ = (
        UniqueConstraint("symbol", "period", "timestamp", name="uq_binance_taker_vol_symbol_period_ts"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    period = Column(String(10), nullable=False)
    buy_vol = Column(Numeric(30, 10), nullable=False)
    sell_vol = Column(Numeric(30, 10), nullable=False)
    buy_sell_ratio = Column(Numeric(10, 4))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)