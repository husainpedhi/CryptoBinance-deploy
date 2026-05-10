from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.taker_volume import BinanceTakerVolume
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_taker_volume(session: Session, rows: list[dict]) -> int:
    if not rows:
        return 0
    stmt = (
        insert(BinanceTakerVolume)
        .values(rows)
        .on_conflict_do_update(
            constraint="uq_binance_taker_vol_symbol_period_ts",
            set_={
                "buy_vol": insert(BinanceTakerVolume).excluded.buy_vol,
                "sell_vol": insert(BinanceTakerVolume).excluded.sell_vol,
                "buy_sell_ratio": insert(BinanceTakerVolume).excluded.buy_sell_ratio,
            },
        )
    )
    session.execute(stmt)
    logger.debug("Upserted %d taker volume rows", len(rows))
    return len(rows)