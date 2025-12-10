from datetime import datetime, timezone
from unittest.mock import MagicMock

from tda_collector.scheduler import run_history_loop


def test_history_loop_paginates_and_inserts(monkeypatch):
    client = MagicMock()
    client.id = "binance"

    row1_ts = datetime(2023, 1, 1, tzinfo=timezone.utc)
    row2_ts = datetime(2023, 1, 1, 0, 1, tzinfo=timezone.utc)

    row = MagicMock()
    row.timestamp = row1_ts
    row2 = MagicMock()
    row2.timestamp = row2_ts

    fetch_calls = []

    limits_seen = []

    def fake_fetch_page(client_arg, symbol, timeframe, since_ms, limit=200):
        fetch_calls.append(since_ms)
        limits_seen.append(limit)
        if len(fetch_calls) == 1:
            return [row, row2]
        return []

    inserted = []

    def fake_insert_rows(client_arg, dataset, table, rows):
        inserted.extend(rows)

    logger = MagicMock()
    tasks = [(client, "BTC/USDT", "1m", 0, int(row2_ts.timestamp() * 1000 + 60000))]

    run_history_loop(
        tasks,
        fetch_page_fn=fake_fetch_page,
        storage_fn=fake_insert_rows,
        logger=logger,
        bq_client=None,
        dataset="crypto",
        table="market_data_ohlcv",
        timeframe_window_ms=60_000,
        page_limit=123,
    )

    assert len(inserted) == 2
    assert fetch_calls[0] == 0
    assert all(limit == 123 for limit in limits_seen)

