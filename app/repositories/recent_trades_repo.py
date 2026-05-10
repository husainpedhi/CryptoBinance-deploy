from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.recent_trades import BinanceRecentTrade
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_recent_trades(session: Session, trades: list[dict]) -> int:
    """Insert recent trades, skip rows with duplicate (symbol, trade_id)."""
    if not trades:
        return 0
    stmt = (
        insert(BinanceRecentTrade)
        .values(trades)
        .on_conflict_do_nothing(constraint="uq_binance_recent_trades_symbol_trade")
    )
    result = session.execute(stmt)
    inserted = result.rowcount if result.rowcount >= 0 else len(trades)
    logger.debug("Inserted %d recent trade rows (attempted %d)", inserted, len(trades))
    return inserted