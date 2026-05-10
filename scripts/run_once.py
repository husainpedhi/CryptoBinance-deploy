#!/usr/bin/env python3
"""
Run every data-collection job exactly once — useful for testing or backfilling.
Usage: python scripts/run_once.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import check_connection
from app.scheduler.jobs import (
    job_fetch_ohlcv,
    job_fetch_order_book,
    job_fetch_recent_trades,
    job_fetch_tickers,
    job_sync_trading_pairs,
)
from app.utils.logger import get_logger

logger = get_logger("run_once")


def main() -> None:
    if not check_connection():
        logger.error("Database not reachable.")
        sys.exit(1)

    logger.info("=== Running all jobs once ===")
    job_sync_trading_pairs()
    job_fetch_tickers()
    job_fetch_ohlcv()
    job_fetch_order_book()
    job_fetch_recent_trades()
    logger.info("=== Done ===")


if __name__ == "__main__":
    main()