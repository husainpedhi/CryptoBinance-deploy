"""Basic smoke tests for the Binance/OKX service layer."""

from app.services.binance_service import (
    _from_okx_instid,
    _parse_funding_rate,
    _parse_futures_kline,
    _parse_kline,
    _parse_liquidation,
    _parse_ls_ratio,
    _parse_oi_hist,
    _parse_taker_vol,
    _parse_ticker,
    _parse_trade,
    _to_okx_bar,
    _to_okx_ccy,
    _to_okx_instid,
)


def test_parse_ticker():
    raw = {
        "symbol": "BTCUSDT",
        "priceChange": "100.00",
        "priceChangePercent": "0.12",
        "weightedAvgPrice": "83000.00",
        "prevClosePrice": "82900.00",
        "lastPrice": "83000.00",
        "bidPrice": "82999.00",
        "askPrice": "83001.00",
        "openPrice": "82900.00",
        "highPrice": "84000.00",
        "lowPrice": "82000.00",
        "volume": "5000.00",
        "quoteVolume": "415000000.00",
        "openTime": 1700000000000,
        "closeTime": 1700086399000,
        "count": 150000,
    }
    result = _parse_ticker(raw)
    assert result["symbol"] == "BTCUSDT"
    assert result["last_price"] == "83000.00"
    assert result["trade_count"] == 150000
    assert result["open_time"] is not None


def test_parse_kline():
    row = [
        1700000000000, "82000.00", "84000.00", "81000.00", "83000.00",
        "5000.00", 1700003599000, "415000000.00", 120000,
        "2500.00", "207500000.00", "0",
    ]
    result = _parse_kline("BTCUSDT", "1h", row)
    assert result["symbol"] == "BTCUSDT"
    assert result["interval"] == "1h"
    assert result["open"] == "82000.00"
    assert result["close"] == "83000.00"
    assert result["trade_count"] == 120000
    assert result["kline_id"] == 1700000000000


def test_parse_trade():
    raw = {
        "id": 987654321,
        "price": "83000.00",
        "qty": "0.05",
        "quoteQty": "4150.00",
        "time": 1700000000000,
        "isBuyerMaker": True,
    }
    result = _parse_trade("BTCUSDT", raw)
    assert result["symbol"] == "BTCUSDT"
    assert result["trade_id"] == 987654321
    assert result["is_buyer_maker"] is True


# ─── OKX symbol helpers ───────────────────────────────────────────────────────

def test_okx_symbol_conversion():
    assert _to_okx_instid("BTCUSDT") == "BTC-USDT-SWAP"
    assert _to_okx_instid("MATICUSDT") == "POL-USDT-SWAP"
    assert _from_okx_instid("BTC-USDT-SWAP") == "BTCUSDT"
    assert _from_okx_instid("POL-USDT-SWAP") == "MATICUSDT"
    assert _to_okx_ccy("BTCUSDT") == "BTC"
    assert _to_okx_ccy("MATICUSDT") == "POL"


# ─── OKX futures parsers ──────────────────────────────────────────────────────

def test_parse_funding_rate_okx():
    raw = {"instId": "BTC-USDT-SWAP", "fundingRate": "0.00010000",
           "fundingTime": "1700000000000", "realizedRate": "0.00009500"}
    result = _parse_funding_rate("BTCUSDT", raw)
    assert result["symbol"] == "BTCUSDT"
    assert result["funding_rate"] == "0.00009500"   # realizedRate, not fundingRate
    assert result["funding_time"] is not None
    assert result["mark_price"] is None


def test_parse_oi_hist_okx():
    row = ["1700000000000", "3553025249.54", "27610940.97"]  # [ts, oi_usd, vol_usd]
    result = _parse_oi_hist("BTCUSDT", "5m", row)
    assert result["symbol"] == "BTCUSDT"
    assert result["period"] == "5m"
    assert result["sum_open_interest"] == "3553025249.54"
    assert result["sum_open_interest_value"] is None
    assert result["timestamp"] is not None


def test_parse_liquidation_okx():
    detail = {"side": "buy", "sz": "0.001", "bkPx": "83000.00",
              "posSide": "short", "ts": "1700000000000"}
    result = _parse_liquidation("BTCUSDT", detail)
    assert result["symbol"] == "BTCUSDT"
    assert result["side"] == "BUY"
    assert result["orig_qty"] == "0.001"
    assert result["price"] == "83000.00"
    assert result["avg_price"] == "83000.00"
    assert result["trade_time"] is not None
    assert result["order_type"] is None


def test_parse_ls_ratio_okx():
    row = ["1700000000000", "1.5"]  # [ts, longShortAccRatio]
    result = _parse_ls_ratio("BTCUSDT", "global", "5m", row)
    assert result["symbol"] == "BTCUSDT"
    assert result["ratio_type"] == "global"
    assert result["period"] == "5m"
    assert result["long_short_ratio"] == "1.5"
    assert result["timestamp"] is not None
    # long + short fractions must sum to 1 and match the source ratio
    long_r, short_r = float(result["long_ratio"]), float(result["short_ratio"])
    assert round(long_r + short_r, 6) == 1.0
    assert round(long_r / short_r, 6) == 1.5


def test_parse_taker_vol_okx():
    row = ["1700000000000", "1000.00", "1500.00"]  # [ts, sellVol, buyVol]
    result = _parse_taker_vol("BTCUSDT", "5m", row)
    assert result["symbol"] == "BTCUSDT"
    assert result["buy_vol"] == "1500.00"
    assert result["sell_vol"] == "1000.00"
    assert result["buy_sell_ratio"] == "1.5"
    assert result["timestamp"] is not None


def test_parse_futures_kline_okx():
    row = ["1700000000000", "82000.00", "84000.00", "81000.00", "83000.00",
           "5000", "415000000.00", "415000000.00", "1"]
    result = _parse_futures_kline("BTCUSDT", "1h", row)
    assert result["symbol"] == "BTCUSDT"
    assert result["interval"] == "1h"
    assert result["open"] == "82000.00"
    assert result["close"] == "83000.00"
    assert result["trade_count"] is None
    assert result["kline_id"] == 1700000000000
    assert result["close_time"] is not None


def test_to_okx_bar():
    assert _to_okx_bar("1h") == "1H"
    assert _to_okx_bar("4h") == "4H"
    assert _to_okx_bar("1d") == "1D"
    assert _to_okx_bar("1m") == "1m"