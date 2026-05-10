#!/usr/bin/env python3
"""
Start the blocking APScheduler — runs all Binance data-collection jobs indefinitely.
Usage: python scripts/run_scheduler.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.database import check_connection
from app.scheduler.scheduler import run_blocking_scheduler
from app.services.binance_service import ping
from app.utils.logger import get_logger

logger = get_logger("run_scheduler")


def main() -> None:
    if not check_connection():
        logger.error("Database not reachable. Run scripts/init_db.py first.")
        sys.exit(1)

    if not ping():
        logger.warning("Binance ping failed — network may be down, continuing anyway.")

    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled via SCHEDULER_ENABLED=false. Exiting.")
        sys.exit(0)

    logger.info("Tracked symbols: %s", settings.tracked_symbols_list)
    logger.info("OHLCV interval: %s  limit: %d", settings.ohlcv_interval, settings.ohlcv_limit)
    run_blocking_scheduler()


if __name__ == "__main__":
    main()