from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.order_book import BinanceOrderBook
from app.utils.logger import get_logger

logger = get_logger(__name__)


def insert_order_book_snapshots(session: Session, snapshots: list[dict]) -> int:
    """Append order book snapshots (time-series)."""
    if not snapshots:
        return 0
    session.bulk_insert_mappings(BinanceOrderBook, snapshots)
    logger.debug("Inserted %d order book snapshots", len(snapshots))
    return len(snapshots)