"""APScheduler — interval-based jobs for all Binance spot and futures data feeds."""

from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.scheduler.jobs import (
    job_fetch_agg_trades, job_fetch_funding_rates, job_fetch_futures_ohlcv,
    job_fetch_liquidations, job_fetch_long_short_ratios, job_fetch_mark_price,
    job_fetch_ohlcv, job_fetch_open_interest, job_fetch_open_interest_hist,
    job_fetch_order_book, job_fetch_order_book_depth, job_fetch_recent_trades,
    job_fetch_taker_volume, job_fetch_tickers, job_sync_trading_pairs,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# (job_fn, interval_seconds, job_id, human_name)
_JOB_SPECS = [
    # ── Spot (every minute) ───────────────────────────────────────────────────
    (job_fetch_tickers,          "ticker_interval_seconds",          "fetch_tickers",           "Spot: 24h tickers"),
    (job_fetch_order_book,       "ticker_interval_seconds",          "fetch_order_book",        "Spot: order book best bid/ask"),
    (job_fetch_mark_price,       "ticker_interval_seconds",          "fetch_mark_price",        "Futures: mark price"),
    (job_fetch_open_interest,    "ticker_interval_seconds",          "fetch_open_interest",     "Futures: open interest (current)"),
    # ── Spot (every 5 minutes) ────────────────────────────────────────────────
    (job_fetch_ohlcv,            "ohlcv_interval_seconds",           "fetch_ohlcv",             "Spot: OHLCV candles"),
    (job_fetch_recent_trades,    "ohlcv_interval_seconds",           "fetch_recent_trades",     "Spot: recent trades"),
    (job_fetch_agg_trades,       "ohlcv_interval_seconds",           "fetch_agg_trades",        "Spot: aggregate trades"),
    (job_fetch_order_book_depth, "ohlcv_interval_seconds",           "fetch_order_book_depth",  "Spot: order book depth"),
    (job_fetch_futures_ohlcv,    "futures_interval_seconds",         "fetch_futures_ohlcv",     "Futures: OHLCV candles"),
    (job_fetch_liquidations,     "futures_interval_seconds",         "fetch_liquidations",      "Futures: liquidations"),
    # ── Every 15 minutes ──────────────────────────────────────────────────────
    (job_fetch_open_interest_hist,  "market_overview_interval_seconds", "fetch_oi_hist",        "Futures: open interest history"),
    (job_fetch_long_short_ratios,   "market_overview_interval_seconds", "fetch_ls_ratios",      "Futures: long/short ratios"),
    (job_fetch_taker_volume,        "market_overview_interval_seconds", "fetch_taker_volume",   "Futures: taker buy/sell volume"),
    # ── Hourly ────────────────────────────────────────────────────────────────
    (job_fetch_funding_rates,    "funding_rate_interval_seconds",    "fetch_funding_rates",     "Futures: funding rates"),
    (job_sync_trading_pairs,     "coin_details_interval_seconds",    "sync_trading_pairs",      "Spot: sync trading pairs"),
]


def _register_jobs(scheduler) -> None:
    # IntervalTrigger's first fire is a full interval after registration, not
    # immediate — so an hourly/15-min job never runs at all if the process gets
    # restarted before it reaches that first checkpoint. Force an immediate
    # first run for every job; the trigger takes over for subsequent runs.
    now = datetime.now(timezone.utc)
    for fn, interval_attr, job_id, name in _JOB_SPECS:
        seconds = getattr(settings, interval_attr)
        scheduler.add_job(
            fn,
            trigger=IntervalTrigger(seconds=seconds),
            id=job_id,
            name=name,
            replace_existing=True,
            max_instances=1,
            next_run_time=now,
            # Default grace (1s) is too tight once several jobs share a
            # next_run_time (e.g. the forced immediate first run above) —
            # a late check silently drops the run instead of executing it.
            misfire_grace_time=60,
        )


def create_background_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    _register_jobs(scheduler)
    return scheduler


def run_blocking_scheduler() -> None:
    scheduler = BlockingScheduler(timezone="UTC")
    _register_jobs(scheduler)

    logger.info("Starting scheduler — %d jobs registered:", len(scheduler.get_jobs()))
    for job in scheduler.get_jobs():
        logger.info("  %-45s  every %s", job.name, job.trigger)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")