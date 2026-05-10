"""Binance data service — spot via python-binance Client, futures via direct requests."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import requests as _requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.logger import get_logger

# ─── Futures HTTP session (public endpoints, no auth) ────────────────────────
_FUTURES_SESSION = _requests.Session()
_FUTURES_SESSION.headers.update({"Content-Type": "application/json"})


def _fapi(path: str, params: dict | None = None) -> Any:
    url = f"{settings.binance_futures_base_url}{path}"
    resp = _FUTURES_SESSION.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

logger = get_logger(__name__)


_client: Optional[Client] = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(
            api_key=settings.binance_api_key or "",
            api_secret=settings.binance_api_secret or "",
            tld="us",
            requests_params={"timeout": 10},
        )
    return _client


def _ts(ms: int | None) -> datetime | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)


# ─── Exchange Info / Trading Pairs ──────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_exchange_info() -> list[dict]:
    """Return parsed trading pair records for all TRADING symbols."""
    logger.info("Fetching exchange info")
    info = _get_client().get_exchange_info()
    pairs = []
    for sym in info["symbols"]:
        parsed = _parse_trading_pair(sym)
        if parsed:
            pairs.append(parsed)
    logger.info("Fetched %d active trading pairs", len(pairs))
    return pairs


def _parse_trading_pair(raw: dict) -> dict | None:
    if raw.get("status") != "TRADING":
        return None
    result: dict[str, Any] = {
        "symbol": raw["symbol"],
        "base_asset": raw["baseAsset"],
        "quote_asset": raw["quoteAsset"],
        "status": raw["status"],
        "is_active": True,
    }
    for f in raw.get("filters", []):
        ft = f.get("filterType")
        if ft == "PRICE_FILTER":
            result["min_price"] = f.get("minPrice")
            result["max_price"] = f.get("maxPrice")
            result["tick_size"] = f.get("tickSize")
        elif ft == "LOT_SIZE":
            result["min_qty"] = f.get("minQty")
            result["max_qty"] = f.get("maxQty")
            result["step_size"] = f.get("stepSize")
    return result


# ─── 24-Hour Tickers ─────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_tickers(symbols: list[str]) -> list[dict]:
    """Fetch 24h ticker stats for the given symbols."""
    logger.info("Fetching 24h tickers for %d symbols", len(symbols))
    raw_list = _get_client().get_ticker()  # returns all symbols
    symbol_set = set(symbols)
    tickers = [_parse_ticker(r) for r in raw_list if r["symbol"] in symbol_set]
    logger.info("Parsed %d tickers", len(tickers))
    return tickers


def _parse_ticker(raw: dict) -> dict:
    return {
        "symbol": raw["symbol"],
        "price_change": raw.get("priceChange"),
        "price_change_percent": raw.get("priceChangePercent"),
        "weighted_avg_price": raw.get("weightedAvgPrice"),
        "prev_close_price": raw.get("prevClosePrice"),
        "last_price": raw["lastPrice"],
        "bid_price": raw.get("bidPrice"),
        "ask_price": raw.get("askPrice"),
        "open_price": raw.get("openPrice"),
        "high_price": raw.get("highPrice"),
        "low_price": raw.get("lowPrice"),
        "volume": raw.get("volume"),
        "quote_volume": raw.get("quoteVolume"),
        "open_time": _ts(raw.get("openTime")),
        "close_time": _ts(raw.get("closeTime")),
        "trade_count": raw.get("count"),
    }


# ─── OHLCV / Klines ──────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_klines(symbol: str, interval: str, limit: int = 100) -> list[dict]:
    """
    Fetch OHLCV candlestick data for a single symbol.

    Binance kline row indices:
      0  open_time, 1 open, 2 high, 3 low, 4 close, 5 volume,
      6  close_time, 7 quote_asset_vol, 8 trades,
      9  taker_buy_base, 10 taker_buy_quote, 11 ignore
    """
    logger.debug("Fetching klines symbol=%s interval=%s", symbol, interval)
    rows = _get_client().get_klines(symbol=symbol, interval=interval, limit=limit)
    return [_parse_kline(symbol, interval, row) for row in rows]


def _parse_kline(symbol: str, interval: str, row: list) -> dict:
    return {
        "symbol": symbol,
        "interval": interval,
        "open_time": _ts(int(row[0])),
        "close_time": _ts(int(row[6])),
        "open": row[1],
        "high": row[2],
        "low": row[3],
        "close": row[4],
        "volume": row[5],
        "quote_asset_volume": row[7],
        "trade_count": int(row[8]),
        "taker_buy_base_volume": row[9],
        "taker_buy_quote_volume": row[10],
        "kline_id": int(row[0]),
    }


# ─── Order Book (best bid/ask) ───────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_order_book_ticker(symbol: str) -> dict:
    """Fetch best bid/ask for a single symbol."""
    raw = _get_client().get_orderbook_ticker(symbol=symbol)
    bid = Decimal(raw["bidPrice"])
    ask = Decimal(raw["askPrice"])
    return {
        "symbol": symbol,
        "bid_price": str(bid),
        "bid_qty": raw["bidQty"],
        "ask_price": str(ask),
        "ask_qty": raw["askQty"],
        "spread": str(ask - bid),
    }


def fetch_order_book_tickers(symbols: list[str]) -> list[dict]:
    """Fetch best bid/ask for multiple symbols (one call per symbol, batched)."""
    logger.info("Fetching order book tickers for %d symbols", len(symbols))
    results = []
    for sym in symbols:
        try:
            results.append(fetch_order_book_ticker(sym))
        except BinanceAPIException as exc:
            logger.warning("Order book fetch failed for %s: %s", sym, exc)
    return results


# ─── Recent Trades ────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_recent_trades(symbol: str, limit: int = 100) -> list[dict]:
    """Fetch the most recent trades for a symbol."""
    logger.debug("Fetching recent trades symbol=%s limit=%d", symbol, limit)
    rows = _get_client().get_recent_trades(symbol=symbol, limit=limit)
    return [_parse_trade(symbol, r) for r in rows]


def _parse_trade(symbol: str, raw: dict) -> dict:
    return {
        "symbol": symbol,
        "trade_id": int(raw["id"]),
        "price": raw["price"],
        "qty": raw["qty"],
        "quote_qty": raw.get("quoteQty"),
        "trade_time": _ts(raw["time"]),
        "is_buyer_maker": raw.get("isBuyerMaker"),
    }


# ─── Server time check ───────────────────────────────────────────────────────

def ping() -> bool:
    try:
        _get_client().ping()
        return True
    except Exception as exc:
        logger.error("Binance ping failed: %s", exc)
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# SPOT ADDITIONS
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Aggregate Trades ─────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_agg_trades(symbol: str, limit: int = 500) -> list[dict]:
    """Compressed aggregate trades — better for volume analysis than raw trades."""
    logger.debug("Fetching agg trades symbol=%s limit=%d", symbol, limit)
    rows = _get_client().get_aggregate_trades(symbol=symbol, limit=limit)
    return [_parse_agg_trade(symbol, r) for r in rows]


def _parse_agg_trade(symbol: str, raw: dict) -> dict:
    return {
        "symbol": symbol,
        "agg_trade_id": int(raw["a"]),
        "price": raw["p"],
        "qty": raw["q"],
        "first_trade_id": int(raw["f"]),
        "last_trade_id": int(raw["l"]),
        "trade_time": _ts(int(raw["T"])),
        "is_buyer_maker": raw["m"],
    }


# ─── Full Order Book Depth ────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_order_book_depth(symbol: str, limit: int = 20) -> list[dict]:
    """
    Fetch full order book depth — returns individual rows per price level.
    limit: 5, 10, 20, 50, 100, 500, 1000 (higher = heavier request).
    """
    logger.debug("Fetching order book depth symbol=%s limit=%d", symbol, limit)
    raw = _get_client().get_order_book(symbol=symbol, limit=limit)
    last_update_id = raw.get("lastUpdateId")
    rows = []
    for lvl, (price, qty) in enumerate(raw.get("bids", []), start=1):
        rows.append({"symbol": symbol, "side": "BID", "level": lvl,
                     "price": price, "qty": qty, "last_update_id": last_update_id})
    for lvl, (price, qty) in enumerate(raw.get("asks", []), start=1):
        rows.append({"symbol": symbol, "side": "ASK", "level": lvl,
                     "price": price, "qty": qty, "last_update_id": last_update_id})
    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# FUTURES (USD-M) — direct requests to fapi.binance.com (public, no auth)
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Funding Rates ────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_funding_rates(symbol: str, limit: int = 100) -> list[dict]:
    """Historical funding rates for a futures symbol (paid every 8 hours)."""
    logger.debug("Fetching funding rates symbol=%s", symbol)
    rows = _fapi("/fapi/v1/fundingRate", {"symbol": symbol, "limit": limit})
    return [_parse_funding_rate(r) for r in rows]


def _parse_funding_rate(raw: dict) -> dict:
    return {
        "symbol": raw["symbol"],
        "funding_time": _ts(int(raw["fundingTime"])),
        "funding_rate": raw["fundingRate"],
        "mark_price": raw.get("markPrice"),
    }


# ─── Open Interest (current) ──────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_open_interest(symbol: str) -> dict:
    """Current open interest for a futures symbol."""
    logger.debug("Fetching open interest symbol=%s", symbol)
    raw = _fapi("/fapi/v1/openInterest", {"symbol": symbol})
    return {
        "symbol": raw["symbol"],
        "open_interest": raw["openInterest"],
    }


# ─── Open Interest History ────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_open_interest_hist(symbol: str, period: str = "5m", limit: int = 30) -> list[dict]:
    """Historical OI aggregated by period from Binance futures data endpoint."""
    logger.debug("Fetching OI hist symbol=%s period=%s", symbol, period)
    rows = _fapi("/futures/data/openInterestHist",
                 {"symbol": symbol, "period": period, "limit": limit})
    return [_parse_oi_hist(r) for r in rows]


def _parse_oi_hist(raw: dict) -> dict:
    return {
        "symbol": raw["symbol"],
        "period": raw.get("period", ""),
        "sum_open_interest": raw["sumOpenInterest"],
        "sum_open_interest_value": raw["sumOpenInterestValue"],
        "timestamp": _ts(int(raw["timestamp"])),
    }


# ─── Long/Short Ratios ────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_long_short_ratio(symbol: str, ratio_type: str, period: str = "5m", limit: int = 30) -> list[dict]:
    """
    Fetch long/short ratio history.
    ratio_type: 'top_accounts' | 'top_positions' | 'global'
    """
    path_map = {
        "top_accounts": "/futures/data/topLongShortAccountRatio",
        "top_positions": "/futures/data/topLongShortPositionRatio",
        "global": "/futures/data/globalLongShortAccountRatio",
    }
    path = path_map[ratio_type]
    logger.debug("Fetching long/short ratio type=%s symbol=%s", ratio_type, symbol)
    rows = _fapi(path, {"symbol": symbol, "period": period, "limit": limit})
    return [_parse_ls_ratio(r, ratio_type) for r in rows]


def _parse_ls_ratio(raw: dict, ratio_type: str) -> dict:
    if ratio_type == "top_positions":
        long_r = raw.get("longPosition", raw.get("longAccount", "0"))
        short_r = raw.get("shortPosition", raw.get("shortAccount", "0"))
    else:
        long_r = raw.get("longAccount", "0")
        short_r = raw.get("shortAccount", "0")
    return {
        "symbol": raw["symbol"],
        "ratio_type": ratio_type,
        "period": raw.get("period", ""),
        "long_ratio": long_r,
        "short_ratio": short_r,
        "long_short_ratio": raw.get("longShortRatio", "0"),
        "timestamp": _ts(int(raw["timestamp"])),
    }


# ─── Taker Buy/Sell Volume ────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_taker_volume(symbol: str, period: str = "5m", limit: int = 30) -> list[dict]:
    """Taker buy vs sell volume — shows who is the aggressor."""
    logger.debug("Fetching taker volume symbol=%s period=%s", symbol, period)
    rows = _fapi("/futures/data/takerbuyVolume",
                 {"symbol": symbol, "period": period, "limit": limit})
    return [_parse_taker_vol(r, symbol) for r in rows]


def _parse_taker_vol(raw: dict, symbol: str) -> dict:
    return {
        "symbol": symbol,
        "period": raw.get("period", ""),
        "buy_vol": raw["buySellRatio"] and raw["buyVol"],
        "sell_vol": raw["sellVol"],
        "buy_sell_ratio": raw.get("buySellRatio"),
        "timestamp": _ts(int(raw["timestamp"])),
    }


# ─── Mark Price ───────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_mark_price(symbol: str) -> dict:
    """Mark price, index price and current funding rate for a futures symbol."""
    logger.debug("Fetching mark price symbol=%s", symbol)
    raw = _fapi("/fapi/v1/premiumIndex", {"symbol": symbol})
    return {
        "symbol": raw["symbol"],
        "mark_price": raw["markPrice"],
        "index_price": raw.get("indexPrice"),
        "estimated_settle_price": raw.get("estimatedSettlePrice"),
        "last_funding_rate": raw.get("lastFundingRate"),
        "next_funding_time": _ts(raw.get("nextFundingTime")),
        "interest_rate": raw.get("interestRate"),
    }


# ─── Futures OHLCV ────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_futures_klines(symbol: str, interval: str, limit: int = 100) -> list[dict]:
    """Futures perpetual contract OHLCV candlestick data."""
    logger.debug("Fetching futures klines symbol=%s interval=%s", symbol, interval)
    rows = _fapi("/fapi/v1/klines",
                 {"symbol": symbol, "interval": interval, "limit": limit})
    return [_parse_futures_kline(symbol, interval, row) for row in rows]


def _parse_futures_kline(symbol: str, interval: str, row: list) -> dict:
    return {
        "symbol": symbol,
        "interval": interval,
        "open_time": _ts(int(row[0])),
        "close_time": _ts(int(row[6])),
        "open": row[1],
        "high": row[2],
        "low": row[3],
        "close": row[4],
        "volume": row[5],
        "quote_asset_volume": row[7],
        "trade_count": int(row[8]),
        "taker_buy_base_volume": row[9],
        "taker_buy_quote_volume": row[10],
        "kline_id": int(row[0]),
    }


# ─── Liquidations ─────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_liquidations(symbol: str, limit: int = 100) -> list[dict]:
    """Historical forced liquidation orders for a futures symbol."""
    logger.debug("Fetching liquidations symbol=%s", symbol)
    rows = _fapi("/fapi/v1/allForceOrders", {"symbol": symbol, "limit": limit})
    return [_parse_liquidation(r) for r in rows]


def _parse_liquidation(raw: dict) -> dict:
    return {
        "symbol": raw["symbol"],
        "side": raw["side"],
        "order_type": raw.get("type"),
        "time_in_force": raw.get("timeInForce"),
        "orig_qty": raw.get("origQty"),
        "price": raw.get("price"),
        "avg_price": raw.get("averagePrice"),
        "order_status": raw.get("status"),
        "last_filled_qty": raw.get("lastFilledQty"),
        "accumulated_qty": raw.get("accumulatedQty"),
        "trade_time": _ts(int(raw["time"])),
    }