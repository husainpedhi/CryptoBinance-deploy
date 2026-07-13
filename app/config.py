from __future__ import annotations
from urllib.parse import quote_plus, urlparse
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── DB backend toggle ──────────────────────────────────────────────────────
    # "local"    → uses DATABASE_URL (localhost Postgres)
    # "supabase" → uses DB_HOST/PORT/NAME/USER/PASSWORD (or SUPABASE_DB_URL override)
    db_backend: str = "local"

    # ── Local Postgres ─────────────────────────────────────────────────────────
    database_url: str = "postgresql://postgres:@localhost:5432/VCrypto"

    # ── Supabase — individual connection params (preferred) ────────────────────
    db_host: str = ""           # e.g. db.bwhajufpdxopwcclbkbh.supabase.co
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str = "postgres"
    db_password: str = ""       # supports special chars like @ — encoded automatically

    # ── Supabase — alternative inputs ─────────────────────────────────────────
    supabase_url: str = ""      # https://<project-ref>.supabase.co  (derives db_host)
    supabase_key: str = ""      # REST API key — NOT the DB password
    supabase_db_password: str = ""  # alias for db_password
    supabase_db_url: str = ""   # full connection string override (takes priority)

    # ── Binance Spot (US) ──────────────────────────────────────────────────────
    binance_api_key: str = ""
    binance_api_secret: str = ""

    # ── OKX (all futures data — Binance fapi.binance.com is US geo-blocked) ──
    okx_base_url: str = "https://www.okx.com/api"

    # ── Scheduler intervals (seconds) ─────────────────────────────────────────
    scheduler_enabled: bool = True
    ticker_interval_seconds: int = Field(default=60, ge=10)
    ohlcv_interval_seconds: int = Field(default=300, ge=60)
    market_overview_interval_seconds: int = Field(default=900, ge=60)
    coin_details_interval_seconds: int = Field(default=3600, ge=300)
    funding_rate_interval_seconds: int = Field(default=3600, ge=60)
    futures_interval_seconds: int = Field(default=300, ge=60)

    # ── Logging ────────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "logs/crypto_research.log"

    # ── Spot symbols ───────────────────────────────────────────────────────────
    tracked_symbols: str = "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,ADAUSDT,DOTUSDT,MATICUSDT,AVAXUSDT,LINKUSDT,UNIUSDT"
    ohlcv_interval: str = "1h"
    ohlcv_limit: int = 100

    # ── Futures symbols ────────────────────────────────────────────────────────
    futures_symbols: str = "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,ADAUSDT,DOTUSDT,MATICUSDT,AVAXUSDT,LINKUSDT,UNIUSDT"
    futures_period: str = "5m"
    futures_ohlcv_interval: str = "1h"
    futures_ohlcv_limit: int = 100
    order_book_depth_limit: int = 20
    agg_trades_limit: int = 500
    funding_rate_limit: int = 100
    liquidation_limit: int = 100

    # ── Derived properties ─────────────────────────────────────────────────────

    @property
    def active_database_url(self) -> str:
        if self.db_backend.lower() == "supabase":
            return self._build_supabase_url()
        return self.database_url

    def _build_supabase_url(self) -> str:
        # Priority 1: explicit full connection string
        if self.supabase_db_url:
            return self.supabase_db_url

        # Resolve host: DB_HOST > derived from SUPABASE_URL
        host = self.db_host
        if not host and self.supabase_url:
            ref = urlparse(self.supabase_url).hostname.split(".")[0]
            host = f"db.{ref}.supabase.co"
        if not host:
            raise ValueError(
                "DB_BACKEND=supabase requires DB_HOST "
                "(e.g. DB_HOST=db.<project-ref>.supabase.co)"
            )

        # Resolve password: DB_PASSWORD > SUPABASE_DB_PASSWORD > SUPABASE_KEY
        password = self.db_password or self.supabase_db_password or self.supabase_key
        if not password:
            raise ValueError(
                "DB_BACKEND=supabase requires DB_PASSWORD.\n"
                "Get it from: Supabase Dashboard → Settings → Database → Database password"
            )

        user = self.db_user or "postgres"
        port = self.db_port or 5432
        name = self.db_name or "postgres"

        # quote_plus encodes special chars (@ → %40, # → %23, etc.)
        return (
            f"postgresql://{user}:{quote_plus(password)}"
            f"@{host}:{port}/{name}?sslmode=require"
        )

    @property
    def tracked_symbols_list(self) -> list[str]:
        return [s.strip() for s in self.tracked_symbols.split(",") if s.strip()]

    @property
    def futures_symbols_list(self) -> list[str]:
        return [s.strip() for s in self.futures_symbols.split(",") if s.strip()]


settings = Settings()