from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.trading_pairs import BinanceTradingPair
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_trading_pairs(session: Session, pairs: list[dict]) -> int:
    """Insert or update trading pairs keyed on symbol."""
    if not pairs:
        return 0
    stmt = (
        insert(BinanceTradingPair)
        .values(pairs)
        .on_conflict_do_update(
            constraint="uq_binance_trading_pairs_symbol",
            set_={
                "base_asset": insert(BinanceTradingPair).excluded.base_asset,
                "quote_asset": insert(BinanceTradingPair).excluded.quote_asset,
                "status": insert(BinanceTradingPair).excluded.status,
                "is_active": insert(BinanceTradingPair).excluded.is_active,
                "min_price": insert(BinanceTradingPair).excluded.min_price,
                "max_price": insert(BinanceTradingPair).excluded.max_price,
                "tick_size": insert(BinanceTradingPair).excluded.tick_size,
                "min_qty": insert(BinanceTradingPair).excluded.min_qty,
                "max_qty": insert(BinanceTradingPair).excluded.max_qty,
                "step_size": insert(BinanceTradingPair).excluded.step_size,
            },
        )
    )
    session.execute(stmt)
    logger.debug("Upserted %d trading pairs", len(pairs))
    return len(pairs)