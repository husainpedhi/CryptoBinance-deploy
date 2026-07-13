"""Binance/OKX data service — spot via python-binance Client, futures via OKX.

Futures routing:
  - All futures endpoints (open interest, funding rates, liquidations, mark
    price, OHLCV, long/short ratio, taker volume) → OKX V5 API (US-accessible).
    Binance's futures API (fapi.binance.com) returns HTTP 451 for US-based
    requests, so none of the futures data can be sourced from it directly.
"""

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

# ─── OKX V5 HTTP session (all futures endpoints) ──────────────────────────────
_OKX_SESSION = _requests.Session()
_OKX_SESSION.headers.update({"Content-Type": "application/json"})

# Symbols that Binance calls MATIC/etc. but OKX uses under a different ticker
_OKX_BASE_RENAMES: dict[str, str] = {"MATIC": "POL"}
_OKX_BASE_RENAMES_REV: dict[str, str] = {v: k for k, v in _OKX_BASE_RENAMES.items()}

# Binance period notation → OKX rubik period values (5m / 1H / 1D only)
_OKX_OI_PERIOD: dict[str, str] = {
    "5m": "5m", "15m": "5m", "30m": "5m",
    "1h": "1H", "4h": "1H", "1d": "1D",
}


def _okx(path: str, params: dict | None = None) -> list:
    url = f"{settings.okx_base_url}{path}"
    resp = _OKX_SESSION.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "0":
        raise ValueError(f"OKX API error {data.get('code')}: {data.get('msg')}")
    return data["data"]


def _to_okx_instid(symbol: str) -> str:
    """BTCUSDT → BTC-USDT-SWAP, MATICUSDT → POL-USDT-SWAP"""
    base = symbol.removesuffix("USDT")
    return f"{_OKX_BASE_RENAMES.get(base, base)}-USDT-SWAP"


def _from_okx_instid(instid: str) -> str:
    """BTC-USDT-SWAP → BTCUSDT, POL-USDT-SWAP → MATICUSDT"""
    base = instid.split("-")[0]
    return f"{_OKX_BASE_RENAMES_REV.get(base, base)}USDT"


def _to_okx_ccy(symbol: str) -> str:
    """BTCUSDT → BTC (for rubik/underlying params), MATICUSDT → POL"""
    base = symbol.removesuffix("USDT")
    return _OKX_BASE_RENAMES.get(base, base)

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
# FUTURES (USD-M) — all via OKX V5 public API (fapi.binance.com is US geo-blocked)
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Funding Rates (OKX) ─────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_funding_rates(symbol: str, limit: int = 100) -> list[dict]:
    """Historical funding rates for a futures symbol via OKX."""
    logger.debug("Fetching funding rates symbol=%s", symbol)
    data = _okx("/v5/public/funding-rate-history",
                {"instId": _to_okx_instid(symbol), "limit": min(limit, 100)})
    return [_parse_funding_rate(symbol, r) for r in data]


def _parse_funding_rate(symbol: str, raw: dict) -> dict:
    return {
        "symbol": symbol,
        "funding_time": _ts(int(raw["fundingTime"])),
        "funding_rate": raw["realizedRate"],  # actual settled rate
        "mark_price": None,
    }


# ─── Open Interest — current snapshot (OKX) ──────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_open_interest(symbol: str) -> dict:
    """Latest open interest snapshot for a futures symbol via OKX."""
    logger.debug("Fetching open interest symbol=%s", symbol)
    data = _okx("/v5/public/open-interest",
                {"instType": "SWAP", "instId": _to_okx_instid(symbol)})
    if not data:
        raise ValueError(f"No open interest data returned for {symbol}")
    return {
        "symbol": symbol,
        "open_interest": data[0]["oiCcy"],  # OI in base currency (coins)
    }


# ─── Open Interest History (OKX) ──────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_open_interest_hist(symbol: str, period: str = "5m", limit: int = 30) -> list[dict]:
    """Historical OI via OKX rubik stats endpoint.

    OKX periods: 5m / 1H / 1D only — _OKX_OI_PERIOD maps finer Binance periods
    to the nearest supported value. Values are USD-denominated (rubik aggregates
    all contracts for the base currency; sumOpenInterestValue stored as None).
    """
    logger.debug("Fetching OI hist symbol=%s period=%s", symbol, period)
    okx_period = _OKX_OI_PERIOD.get(period, "5m")
    data = _okx("/v5/rubik/stat/contracts/open-interest-volume",
                {"ccy": _to_okx_ccy(symbol), "period": okx_period, "limit": limit})
    return [_parse_oi_hist(symbol, okx_period, row) for row in data]


def _parse_oi_hist(symbol: str, period: str, row: list) -> dict:
    return {
        "symbol": symbol,
        "period": period,
        "sum_open_interest": row[1],  # USD-denominated OI (rubik only provides USD)
        "sum_open_interest_value": None,
        "timestamp": _ts(int(row[0])),
    }


# ─── Long/Short Ratios (OKX) ──────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_long_short_ratio(symbol: str, ratio_type: str, period: str = "5m", limit: int = 30) -> list[dict]:
    """
    Fetch long/short ratio history via OKX.

    ratio_type: 'top_accounts' | 'top_positions' | 'global'
    OKX's rubik stats only expose a single aggregate account long/short ratio
    (no top-trader vs. all-trader breakdown like Binance), so all three
    ratio_types are sourced from the same OKX series — top_accounts and
    top_positions no longer diverge from global post-migration.
    """
    logger.debug("Fetching long/short ratio type=%s symbol=%s", ratio_type, symbol)
    okx_period = _OKX_OI_PERIOD.get(period, "5m")
    data = _okx("/v5/rubik/stat/contracts/long-short-account-ratio-contract",
                {"ccy": _to_okx_ccy(symbol), "period": okx_period, "limit": limit})
    return [_parse_ls_ratio(symbol, ratio_type, okx_period, row) for row in data]


def _parse_ls_ratio(symbol: str, ratio_type: str, period: str, row: list) -> dict:
    """row: [ts, longShortAccRatio]. Binance's separate long/short account
    fractions are derived from OKX's single ratio (long + short == 1):
    long = ratio / (1 + ratio), short = 1 / (1 + ratio)."""
    ratio = Decimal(row[1])
    long_r = ratio / (1 + ratio)
    short_r = 1 / (1 + ratio)
    return {
        "symbol": symbol,
        "ratio_type": ratio_type,
        "period": period,
        "long_ratio": str(long_r),
        "short_ratio": str(short_r),
        "long_short_ratio": str(ratio),
        "timestamp": _ts(int(row[0])),
    }


# ─── Taker Buy/Sell Volume (OKX) ──────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_taker_volume(symbol: str, period: str = "5m", limit: int = 30) -> list[dict]:
    """Taker buy vs sell volume via OKX rubik stats — shows who is the aggressor.

    OKX periods: 5m / 1H / 1D only — reuses _OKX_OI_PERIOD mapping.
    """
    logger.debug("Fetching taker volume symbol=%s period=%s", symbol, period)
    okx_period = _OKX_OI_PERIOD.get(period, "5m")
    data = _okx("/v5/rubik/stat/taker-volume",
                {"ccy": _to_okx_ccy(symbol), "instType": "CONTRACTS",
                 "period": okx_period, "limit": limit})
    return [_parse_taker_vol(symbol, okx_period, row) for row in data]


def _parse_taker_vol(symbol: str, period: str, row: list) -> dict:
    """row: [ts, sellVol, buyVol]."""
    sell_vol = Decimal(row[1])
    buy_vol = Decimal(row[2])
    return {
        "symbol": symbol,
        "period": period,
        "buy_vol": str(buy_vol),
        "sell_vol": str(sell_vol),
        "buy_sell_ratio": str(buy_vol / sell_vol) if sell_vol else None,
        "timestamp": _ts(int(row[0])),
    }


# ─── Mark Price (OKX) ──────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_mark_price(symbol: str) -> dict:
    """Mark price and current funding rate for a futures symbol via OKX."""
    logger.debug("Fetching mark price symbol=%s", symbol)
    inst_id = _to_okx_instid(symbol)
    mark_data = _okx("/v5/public/mark-price", {"instType": "SWAP", "instId": inst_id})
    if not mark_data:
        raise ValueError(f"No mark price data returned for {symbol}")
    funding_data = _okx("/v5/public/funding-rate", {"instId": inst_id})
    funding = funding_data[0] if funding_data else {}
    return {
        "symbol": symbol,
        "mark_price": mark_data[0]["markPx"],
        "index_price": None,             # no OKX equivalent on this endpoint
        "estimated_settle_price": None,  # perpetuals have no settlement — no OKX equivalent
        "last_funding_rate": funding.get("fundingRate"),
        "next_funding_time": _ts(int(funding["nextFundingTime"])) if funding.get("nextFundingTime") else None,
        "interest_rate": None,           # no OKX equivalent exposed publicly
    }


# ─── Futures OHLCV (OKX) ───────────────────────────────────────────────────────

# Binance interval unit → OKX candle 'bar' duration, in milliseconds (for close_time)
_MS_PER_UNIT: dict[str, int] = {"m": 60_000, "h": 3_600_000, "d": 86_400_000, "w": 604_800_000}


def _to_okx_bar(interval: str) -> str:
    """Binance interval notation → OKX candle 'bar' notation (uppercase unit, minutes/month unchanged)."""
    unit = interval[-1]
    return interval[:-1] + unit.upper() if unit in ("h", "d", "w") else interval


def _interval_ms(interval: str) -> int:
    """Approximate duration of a Binance-style interval string, in milliseconds."""
    unit = interval[-1]
    if unit == "M":  # calendar month — approximate as 30 days
        return 30 * _MS_PER_UNIT["d"]
    return int(interval[:-1]) * _MS_PER_UNIT[unit]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_futures_klines(symbol: str, interval: str, limit: int = 100) -> list[dict]:
    """Futures perpetual contract OHLCV candlestick data via OKX."""
    logger.debug("Fetching futures klines symbol=%s interval=%s", symbol, interval)
    rows = _okx("/v5/market/candles",
                {"instId": _to_okx_instid(symbol), "bar": _to_okx_bar(interval), "limit": limit})
    return [_parse_futures_kline(symbol, interval, row) for row in rows]


def _parse_futures_kline(symbol: str, interval: str, row: list) -> dict:
    """row: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]. OKX candles carry
    no trade count or taker buy/sell breakdown — those fields have no equivalent."""
    open_time_ms = int(row[0])
    return {
        "symbol": symbol,
        "interval": interval,
        "open_time": _ts(open_time_ms),
        "close_time": _ts(open_time_ms + _interval_ms(interval) - 1),
        "open": row[1],
        "high": row[2],
        "low": row[3],
        "close": row[4],
        "volume": row[5],
        "quote_asset_volume": row[7],
        "trade_count": None,             # no OKX equivalent
        "taker_buy_base_volume": None,   # no OKX equivalent
        "taker_buy_quote_volume": None,  # no OKX equivalent
        "kline_id": open_time_ms,
    }


# ─── Liquidations (OKX) ───────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
def fetch_liquidations(symbol: str, limit: int = 100) -> list[dict]:
    """Recent forced liquidations for a futures symbol via OKX.

    OKX groups fills at the same price into a details[] list per instrument;
    we flatten to one row per fill. Binance-specific order fields are None.
    """
    logger.debug("Fetching liquidations symbol=%s", symbol)
    ccy = _to_okx_ccy(symbol)
    data = _okx("/v5/public/liquidation-orders",
                {"instType": "SWAP", "uly": f"{ccy}-USDT",
                 "state": "filled", "limit": min(limit, 100)})
    results = []
    for item in data:
        if "instId" not in item:
            # OKX uses {'$ref': '$.data[0]'} for repeated instrument entries — skip them
            continue
        inst_symbol = _from_okx_instid(item["instId"])
        for detail in item.get("details", []):
            results.append(_parse_liquidation(inst_symbol, detail))
    return results


def _parse_liquidation(symbol: str, detail: dict) -> dict:
    return {
        "symbol": symbol,
        "side": detail["side"].upper(),  # OKX: "buy"/"sell" → "BUY"/"SELL"
        "order_type": None,
        "time_in_force": None,
        "orig_qty": detail["sz"],
        "price": detail["bkPx"],         # bankruptcy price
        "avg_price": detail["bkPx"],
        "order_status": None,
        "last_filled_qty": detail["sz"],
        "accumulated_qty": None,
        "trade_time": _ts(int(detail["ts"])),
    }