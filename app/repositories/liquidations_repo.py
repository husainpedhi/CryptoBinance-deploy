from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.liquidations import BinanceLiquidation
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_liquidations(session: Session, rows: list[dict]) -> int:
    if not rows:
        return 0
    stmt = (
        insert(BinanceLiquidation)
        .values(rows)
        .on_conflict_do_nothing(constraint="uq_binance_liquidation_symbol_time_price_qty")
    )
    session.execute(stmt)
    logger.debug("Upserted %d liquidation rows", len(rows))
    return len(rows)