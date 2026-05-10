from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.open_interest import BinanceOpenInterest
from app.utils.logger import get_logger

logger = get_logger(__name__)


def insert_open_interest(session: Session, rows: list[dict]) -> int:
    if not rows:
        return 0
    session.bulk_insert_mappings(BinanceOpenInterest, rows)
    logger.debug("Inserted %d open interest snapshots", len(rows))
    return len(rows)