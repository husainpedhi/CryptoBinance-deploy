from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.order_book_depth import BinanceOrderBookDepth
from app.utils.logger import get_logger

logger = get_logger(__name__)


def insert_order_book_depth(session: Session, rows: list[dict]) -> int:
    if not rows:
        return 0
    session.bulk_insert_mappings(BinanceOrderBookDepth, rows)
    logger.debug("Inserted %d order book depth rows", len(rows))
    return len(rows)