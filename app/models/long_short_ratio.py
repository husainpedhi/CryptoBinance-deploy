from sqlalchemy import Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.models.base import Base


class BinanceLongShortRatio(Base):
    """
    Long/short ratio snapshots — three types stored together:
      top_accounts  : top trader long/short account ratio
      top_positions : top trader long/short position ratio
      global        : all traders long/short account ratio
    """

    __tablename__ = "binance_long_short_ratio"
    __table_args__ = (
        UniqueConstraint(
            "symbol", "ratio_type", "period", "timestamp",
            name="uq_binance_ls_ratio_symbol_type_period_ts",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    ratio_type = Column(String(20), nullable=False)   # top_accounts | top_positions | global
    period = Column(String(10), nullable=False)
    long_ratio = Column(Numeric(10, 4), nullable=False)
    short_ratio = Column(Numeric(10, 4), nullable=False)
    long_short_ratio = Column(Numeric(10, 4), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)