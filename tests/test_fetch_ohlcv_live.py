from datetime import datetime, timezone
from unittest.mock import MagicMock

from tda_collector import adapter


def test_fetch_ohlcv_live_formats_previous_and_current():
    client = MagicMock()
    client.id = "binance"
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    client.fetch_ohlcv.return_value = [
        [now_ms - 120000, 1, 2, 0.5, 1.5, 100],
        [now_ms - 60000, 1.5, 2.5, 1.0, 2.0, 120],
    ]

    prev_bar, curr_bar = adapter.fetch_last_two(client, "BTC/USDT", "1m")

    assert prev_bar.exchange == "binance"
    assert prev_bar.symbol == "BTC/USDT"
    assert prev_bar.timeframe == "1m"
    assert prev_bar.open == 1
    assert curr_bar.close == 2.0
    assert prev_bar.timestamp < curr_bar.timestamp

