from sqlalchemy import Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.models.base import Base


class BinanceFundingRate(Base):
    """Futures funding rate history — paid every 8 hours per symbol."""

    __tablename__ = "binance_funding_rates"
    __table_args__ = (
        UniqueConstraint("symbol", "funding_time", name="uq_binance_funding_rates_symbol_time"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    funding_time = Column(DateTime(timezone=True), nullable=False, index=True)
    funding_rate = Column(Numeric(20, 10), nullable=False)
    mark_price = Column(Numeric(30, 10))