#!/usr/bin/env python3
"""
Run Alembic migrations and verify the database is ready.
Usage: python scripts/init_db.py
"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import check_connection
from app.utils.logger import get_logger

logger = get_logger("init_db")


def main() -> None:
    logger.info("Checking database connection...")
    if not check_connection():
        logger.error("Cannot connect to VCrypto. Is Postgres running?")
        sys.exit(1)

    logger.info("Running Alembic migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Migration failed:\n%s", result.stderr)
        sys.exit(1)

    logger.info("Migration output:\n%s", result.stdout or result.stderr)
    logger.info("Database initialised successfully.")


if __name__ == "__main__":
    main()