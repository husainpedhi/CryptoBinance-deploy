from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.models.base import Base


class BinanceFuturesOHLCV(Base):
    """Futures perpetual contract OHLCV candlestick data."""

    __tablename__ = "binance_futures_ohlcv"
    __table_args__ = (
        UniqueConstraint("symbol", "interval", "open_time", name="uq_binance_futures_ohlcv_symbol_interval_open"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False)
    open_time = Column(DateTime(timezone=True), nullable=False, index=True)
    close_time = Column(DateTime(timezone=True), nullable=False)
    open = Column(Numeric(30, 10), nullable=False)
    high = Column(Numeric(30, 10), nullable=False)
    low = Column(Numeric(30, 10), nullable=False)
    close = Column(Numeric(30, 10), nullable=False)
    volume = Column(Numeric(30, 10), nullable=False)
    quote_asset_volume = Column(Numeric(30, 10))
    trade_count = Column(Integer)
    taker_buy_base_volume = Column(Numeric(30, 10))
    taker_buy_quote_volume = Column(Numeric(30, 10))
    kline_id = Column(BigInteger)