from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_db_url = settings.active_database_url
_is_supabase = settings.db_backend.lower() == "supabase"

# Supabase (transaction pooler) needs a smaller pool and no server-side cursors.
engine = create_engine(
    _db_url,
    pool_size=5 if _is_supabase else 10,
    max_overflow=10 if _is_supabase else 20,
    pool_pre_ping=True,
    pool_recycle=300 if _is_supabase else 3600,
    echo=False,
    # Supabase pooler sits in front of Postgres — keepalives help stability
    connect_args={"connect_timeout": 10} if _is_supabase else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connection() -> bool:
    backend = settings.db_backend.upper()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection OK — backend=%s", backend)
        return True
    except Exception as exc:
        logger.error("Database connection failed [%s]: %s", backend, exc)
        return False