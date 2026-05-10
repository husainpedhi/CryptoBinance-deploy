"""Scheduler job definitions — each job fetches from Binance and writes to VCrypto."""

import time
from datetime import datetime, timezone

from app.config import settings
from app.database import get_db
from app.repositories import (
    agg_trades_repo, funding_rates_repo, futures_ohlcv_repo,
    liquidations_repo, long_short_ratio_repo, mark_price_repo,
    ohlcv_repo, open_interest_hist_repo, open_interest_repo,
    order_book_depth_repo, order_book_repo, recent_trades_repo,
    scheduler_log_repo, taker_volume_repo, ticker_repo, trading_pairs_repo,
)
from app.services import binance_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _run_job(job_name: str, fn, *args, **kwargs) -> int:
    started = datetime.now(tz=timezone.utc)
    t0 = time.monotonic()
    try:
        count = fn(*args, **kwargs)
        elapsed = time.monotonic() - t0
        with get_db() as session:
            scheduler_log_repo.log_job(session, job_name=job_name, status="success",
                                       records_processed=count,
                                       duration_seconds=round(elapsed, 3), started_at=started)
        logger.info("[%s] OK — %d records in %.2fs", job_name, count, elapsed)
        return count
    except Exception as exc:
        elapsed = time.monotonic() - t0
        logger.error("[%s] FAILED after %.2fs: %s", job_name, elapsed, exc)
        try:
            with get_db() as session:
                scheduler_log_repo.log_job(session, job_name=job_name, status="error",
                                           records_processed=0,
                                           duration_seconds=round(elapsed, 3),
                                           error_message=str(exc)[:2000], started_at=started)
        except Exception as log_exc:
            logger.error("Failed to write scheduler log: %s", log_exc)
        return 0


# ─── Spot Jobs ────────────────────────────────────────────────────────────────

def _do_fetch_tickers() -> int:
    tickers = binance_service.fetch_tickers(settings.tracked_symbols_list)
    if not tickers:
        return 0
    with get_db() as session:
        return ticker_repo.insert_tickers(session, tickers)


def _do_fetch_ohlcv() -> int:
    total = 0
    for symbol in settings.tracked_symbols_list:
        candles = binance_service.fetch_klines(symbol, settings.ohlcv_interval, settings.ohlcv_limit)
        with get_db() as session:
            total += ohlcv_repo.upsert_ohlcv(session, candles)
    return total


def _do_fetch_order_book() -> int:
    snapshots = binance_service.fetch_order_book_tickers(settings.tracked_symbols_list)
    if not snapshots:
        return 0
    with get_db() as session:
        return order_book_repo.insert_order_book_snapshots(session, snapshots)


def _do_fetch_recent_trades() -> int:
    total = 0
    for symbol in settings.tracked_symbols_list:
        trades = binance_service.fetch_recent_trades(symbol, limit=100)
        with get_db() as session:
            total += recent_trades_repo.upsert_recent_trades(session, trades)
    return total


def _do_sync_trading_pairs() -> int:
    pairs = binance_service.fetch_exchange_info()
    with get_db() as session:
        return trading_pairs_repo.upsert_trading_pairs(session, pairs)


def _do_fetch_agg_trades() -> int:
    total = 0
    for symbol in settings.tracked_symbols_list:
        trades = binance_service.fetch_agg_trades(symbol, limit=settings.agg_trades_limit)
        with get_db() as session:
            total += agg_trades_repo.upsert_agg_trades(session, trades)
    return total


def _do_fetch_order_book_depth() -> int:
    total = 0
    for symbol in settings.tracked_symbols_list:
        rows = binance_service.fetch_order_book_depth(symbol, limit=settings.order_book_depth_limit)
        with get_db() as session:
            total += order_book_depth_repo.insert_order_book_depth(session, rows)
    return total


# ─── Futures Jobs ─────────────────────────────────────────────────────────────

def _do_fetch_funding_rates() -> int:
    total = 0
    for symbol in settings.futures_symbols_list:
        rates = binance_service.fetch_funding_rates(symbol, limit=settings.funding_rate_limit)
        with get_db() as session:
            total += funding_rates_repo.upsert_funding_rates(session, rates)
    return total


def _do_fetch_open_interest() -> int:
    rows = []
    for symbol in settings.futures_symbols_list:
        try:
            rows.append(binance_service.fetch_open_interest(symbol))
        except Exception as exc:
            logger.warning("OI fetch failed for %s: %s", symbol, exc)
    if not rows:
        return 0
    with get_db() as session:
        return open_interest_repo.insert_open_interest(session, rows)


def _do_fetch_open_interest_hist() -> int:
    total = 0
    for symbol in settings.futures_symbols_list:
        rows = binance_service.fetch_open_interest_hist(symbol, period=settings.futures_period, limit=30)
        with get_db() as session:
            total += open_interest_hist_repo.upsert_open_interest_hist(session, rows)
    return total


def _do_fetch_long_short_ratios() -> int:
    total = 0
    for symbol in settings.futures_symbols_list:
        for ratio_type in ("top_accounts", "top_positions", "global"):
            try:
                rows = binance_service.fetch_long_short_ratio(
                    symbol, ratio_type, period=settings.futures_period, limit=30)
                with get_db() as session:
                    total += long_short_ratio_repo.upsert_long_short_ratios(session, rows)
            except Exception as exc:
                logger.warning("L/S ratio %s/%s failed: %s", symbol, ratio_type, exc)
    return total


def _do_fetch_taker_volume() -> int:
    total = 0
    for symbol in settings.futures_symbols_list:
        rows = binance_service.fetch_taker_volume(symbol, period=settings.futures_period, limit=30)
        with get_db() as session:
            total += taker_volume_repo.upsert_taker_volume(session, rows)
    return total


def _do_fetch_mark_price() -> int:
    rows = []
    for symbol in settings.futures_symbols_list:
        try:
            rows.append(binance_service.fetch_mark_price(symbol))
        except Exception as exc:
            logger.warning("Mark price fetch failed for %s: %s", symbol, exc)
    if not rows:
        return 0
    with get_db() as session:
        return mark_price_repo.insert_mark_prices(session, rows)


def _do_fetch_futures_ohlcv() -> int:
    total = 0
    for symbol in settings.futures_symbols_list:
        candles = binance_service.fetch_futures_klines(
            symbol, settings.futures_ohlcv_interval, settings.futures_ohlcv_limit)
        with get_db() as session:
            total += futures_ohlcv_repo.upsert_futures_ohlcv(session, candles)
    return total


def _do_fetch_liquidations() -> int:
    total = 0
    for symbol in settings.futures_symbols_list:
        rows = binance_service.fetch_liquidations(symbol, limit=settings.liquidation_limit)
        with get_db() as session:
            total += liquidations_repo.upsert_liquidations(session, rows)
    return total


# ─── Public entry points ──────────────────────────────────────────────────────

def job_fetch_tickers():          _run_job("fetch_tickers", _do_fetch_tickers)
def job_fetch_ohlcv():            _run_job("fetch_ohlcv", _do_fetch_ohlcv)
def job_fetch_order_book():       _run_job("fetch_order_book", _do_fetch_order_book)
def job_fetch_recent_trades():    _run_job("fetch_recent_trades", _do_fetch_recent_trades)
def job_sync_trading_pairs():     _run_job("sync_trading_pairs", _do_sync_trading_pairs)
def job_fetch_agg_trades():       _run_job("fetch_agg_trades", _do_fetch_agg_trades)
def job_fetch_order_book_depth(): _run_job("fetch_order_book_depth", _do_fetch_order_book_depth)
def job_fetch_funding_rates():    _run_job("fetch_funding_rates", _do_fetch_funding_rates)
def job_fetch_open_interest():    _run_job("fetch_open_interest", _do_fetch_open_interest)
def job_fetch_open_interest_hist(): _run_job("fetch_open_interest_hist", _do_fetch_open_interest_hist)
def job_fetch_long_short_ratios(): _run_job("fetch_long_short_ratios", _do_fetch_long_short_ratios)
def job_fetch_taker_volume():     _run_job("fetch_taker_volume", _do_fetch_taker_volume)
def job_fetch_mark_price():       _run_job("fetch_mark_price", _do_fetch_mark_price)
def job_fetch_futures_ohlcv():    _run_job("fetch_futures_ohlcv", _do_fetch_futures_ohlcv)
def job_fetch_liquidations():     _run_job("fetch_liquidations", _do_fetch_liquidations)