from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.long_short_ratio import BinanceLongShortRatio
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_long_short_ratios(session: Session, rows: list[dict]) -> int:
    if not rows:
        return 0
    stmt = (
        insert(BinanceLongShortRatio)
        .values(rows)
        .on_conflict_do_update(
            constraint="uq_binance_ls_ratio_symbol_type_period_ts",
            set_={
                "long_ratio": insert(BinanceLongShortRatio).excluded.long_ratio,
                "short_ratio": insert(BinanceLongShortRatio).excluded.short_ratio,
                "long_short_ratio": insert(BinanceLongShortRatio).excluded.long_short_ratio,
            },
        )
    )
    session.execute(stmt)
    logger.debug("Upserted %d long/short ratio rows", len(rows))
    return len(rows)