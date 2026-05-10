from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.mark_price import BinanceMarkPrice
from app.utils.logger import get_logger

logger = get_logger(__name__)


def insert_mark_prices(session: Session, rows: list[dict]) -> int:
    if not rows:
        return 0
    session.bulk_insert_mappings(BinanceMarkPrice, rows)
    logger.debug("Inserted %d mark price snapshots", len(rows))
    return len(rows)