from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.funding_rates import BinanceFundingRate
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_funding_rates(session: Session, rates: list[dict]) -> int:
    if not rates:
        return 0
    stmt = (
        insert(BinanceFundingRate)
        .values(rates)
        .on_conflict_do_update(
            constraint="uq_binance_funding_rates_symbol_time",
            set_={
                "funding_rate": insert(BinanceFundingRate).excluded.funding_rate,
                "mark_price": insert(BinanceFundingRate).excluded.mark_price,
            },
        )
    )
    session.execute(stmt)
    logger.debug("Upserted %d funding rate rows", len(rates))
    return len(rates)