from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.open_interest_hist import BinanceOpenInterestHist
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_open_interest_hist(session: Session, rows: list[dict]) -> int:
    if not rows:
        return 0
    stmt = (
        insert(BinanceOpenInterestHist)
        .values(rows)
        .on_conflict_do_update(
            constraint="uq_binance_oi_hist_symbol_period_ts",
            set_={
                "sum_open_interest": insert(BinanceOpenInterestHist).excluded.sum_open_interest,
                "sum_open_interest_value": insert(BinanceOpenInterestHist).excluded.sum_open_interest_value,
            },
        )
    )
    session.execute(stmt)
    logger.debug("Upserted %d OI hist rows", len(rows))
    return len(rows)