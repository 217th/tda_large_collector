from unittest.mock import MagicMock

from tda_collector.models import OHLCVRecord
from tda_collector.storage import insert_rows
from datetime import datetime, timezone


def test_bigquery_insert_payload_structure(monkeypatch):
    client = MagicMock()
    rows_to_insert = []

    def fake_insert_rows_json(table_id, payload):
        rows_to_insert.extend(payload)
        return []

    client.insert_rows_json.side_effect = fake_insert_rows_json
    client.project = "test-project"

    record = OHLCVRecord(
        timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
        exchange="binance",
        symbol="BTC/USDT",
        timeframe="1m",
        open=1.0,
        high=2.0,
        low=0.5,
        close=1.5,
        volume=100.0,
        ingested_at=datetime(2023, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
    )

    insert_rows(client, "crypto", "market_data_ohlcv", [record])

    assert rows_to_insert[0]["exchange"] == "binance"
    assert rows_to_insert[0]["symbol"] == "BTC/USDT"
    assert rows_to_insert[0]["timeframe"] == "1m"
    assert rows_to_insert[0]["open"] == 1.0
    assert "ingested_at" in rows_to_insert[0]

