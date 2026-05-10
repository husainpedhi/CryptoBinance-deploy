from sqlalchemy import Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.models.base import Base


class BinanceOpenInterestHist(Base):
    """Historical open interest aggregated by period from Binance futures data API."""

    __tablename__ = "binance_open_interest_hist"
    __table_args__ = (
        UniqueConstraint("symbol", "period", "timestamp", name="uq_binance_oi_hist_symbol_period_ts"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    period = Column(String(10), nullable=False)       # 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
    sum_open_interest = Column(Numeric(30, 10), nullable=False)
    sum_open_interest_value = Column(Numeric(30, 4))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)