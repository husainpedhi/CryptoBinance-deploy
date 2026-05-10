#!/usr/bin/env python3
"""
Diagnose the database connection and print setup instructions.
Usage: python scripts/check_db.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("check_db")


def _mask(url: str) -> str:
    return re.sub(r"://([^:]*):([^@]*)@", r"://\1:****@", url)


def main() -> None:
    backend = settings.db_backend.lower()
    print(f"\n{'='*60}")
    print(f"  DB_BACKEND = {backend.upper()}")
    print(f"{'='*60}\n")

    # ── Build and show the connection URL ─────────────────────────────────────
    try:
        url = settings.active_database_url
        print(f"  Connection URL : {_mask(url)}\n")
    except ValueError as exc:
        print(f"  [CONFIG ERROR] {exc}\n")
        _print_supabase_instructions()
        sys.exit(1)

    # ── Attempt connection ────────────────────────────────────────────────────
    from app.database import check_connection
    ok = check_connection()

    if ok:
        print("\n  ✓  Connection successful!\n")
        if backend == "supabase":
            print("  Next step: run the migration against Supabase:")
            print("    DB_BACKEND=supabase python scripts/init_db.py\n")
        else:
            print("  Next step: start the data collector:")
            print("    python scripts/run_scheduler.py\n")
    else:
        print("\n  ✗  Connection failed.\n")
        if backend == "supabase":
            _print_supabase_instructions()
        else:
            print("  Make sure Postgres.app is running and VCrypto database exists.")
            print("  Verify: DATABASE_URL in .env\n")
        sys.exit(1)


def _print_supabase_instructions() -> None:
    print("  HOW TO FIX — Supabase setup:")
    print()
    print("  Option A (recommended) — paste the full connection string:")
    print("    1. Go to Supabase Dashboard → Settings → Database")
    print("    2. Copy the 'Connection string' (URI format)")
    print("    3. Add to .env:")
    print("         SUPABASE_DB_URL=postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres?sslmode=require")
    print()
    print("  Option B — provide just the DB password:")
    print("    1. Go to Supabase Dashboard → Settings → Database → Database password")
    print("    2. Add to .env:")
    print("         SUPABASE_DB_PASSWORD=<your-database-password>")
    print()
    print("  NOTE: SUPABASE_KEY is the REST API key — it is NOT the database password.")
    print()


if __name__ == "__main__":
    main()