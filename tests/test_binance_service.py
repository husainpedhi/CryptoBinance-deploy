"""Basic smoke tests for the Binance service layer."""

from app.services.binance_service import _parse_ticker, _parse_kline, _parse_trade


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