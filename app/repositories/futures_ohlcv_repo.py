from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.futures_ohlcv import BinanceFuturesOHLCV
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_futures_ohlcv(session: Session, candles: list[dict]) -> int:
    if not candles:
        return 0
    stmt = (
        insert(BinanceFuturesOHLCV)
        .values(candles)
        .on_conflict_do_update(
            constraint="uq_binance_futures_ohlcv_symbol_interval_open",
            set_={
                "close_time": insert(BinanceFuturesOHLCV).excluded.close_time,
                "open": insert(BinanceFuturesOHLCV).excluded.open,
                "high": insert(BinanceFuturesOHLCV).excluded.high,
                "low": insert(BinanceFuturesOHLCV).excluded.low,
                "close": insert(BinanceFuturesOHLCV).excluded.close,
                "volume": insert(BinanceFuturesOHLCV).excluded.volume,
                "quote_asset_volume": insert(BinanceFuturesOHLCV).excluded.quote_asset_volume,
                "trade_count": insert(BinanceFuturesOHLCV).excluded.trade_count,
                "taker_buy_base_volume": insert(BinanceFuturesOHLCV).excluded.taker_buy_base_volume,
                "taker_buy_quote_volume": insert(BinanceFuturesOHLCV).excluded.taker_buy_quote_volume,
            },
        )
    )
    session.execute(stmt)
    logger.debug("Upserted %d futures OHLCV rows", len(candles))
    return len(candles)