from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.ticker import BinanceTicker
from app.utils.logger import get_logger

logger = get_logger(__name__)


def insert_tickers(session: Session, tickers: list[dict]) -> int:
    """Append ticker snapshots (time-series — no dedup needed)."""
    if not tickers:
        return 0
    session.bulk_insert_mappings(BinanceTicker, tickers)
    logger.debug("Inserted %d ticker records", len(tickers))
    return len(tickers)