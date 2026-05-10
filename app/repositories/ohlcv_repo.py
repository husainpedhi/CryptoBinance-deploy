from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.ohlcv import BinanceOHLCV
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_ohlcv(session: Session, candles: list[dict]) -> int:
    """Insert OHLCV rows, skip duplicates on (symbol, interval, open_time)."""
    if not candles:
        return 0
    stmt = (
        insert(BinanceOHLCV)
        .values(candles)
        .on_conflict_do_update(
            constraint="uq_binance_ohlcv_symbol_interval_open",
            set_={
                "close_time": insert(BinanceOHLCV).excluded.close_time,
                "open": insert(BinanceOHLCV).excluded.open,
                "high": insert(BinanceOHLCV).excluded.high,
                "low": insert(BinanceOHLCV).excluded.low,
                "close": insert(BinanceOHLCV).excluded.close,
                "volume": insert(BinanceOHLCV).excluded.volume,
                "quote_asset_volume": insert(BinanceOHLCV).excluded.quote_asset_volume,
                "trade_count": insert(BinanceOHLCV).excluded.trade_count,
                "taker_buy_base_volume": insert(BinanceOHLCV).excluded.taker_buy_base_volume,
                "taker_buy_quote_volume": insert(BinanceOHLCV).excluded.taker_buy_quote_volume,
            },
        )
    )
    session.execute(stmt)
    logger.debug("Upserted %d OHLCV rows", len(candles))
    return len(candles)