from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.agg_trades import BinanceAggTrade
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_agg_trades(session: Session, trades: list[dict]) -> int:
    if not trades:
        return 0
    stmt = (
        insert(BinanceAggTrade)
        .values(trades)
        .on_conflict_do_nothing(constraint="uq_binance_agg_trades_symbol_id")
    )
    session.execute(stmt)
    logger.debug("Upserted %d agg trade rows", len(trades))
    return len(trades)