from datetime import datetime, timezone
from unittest.mock import MagicMock

from tda_collector.models import OHLCVRecord
from tda_collector import storage
from tda_collector.storage import ensure_table, insert_rows


class DummyTable:
    def __init__(self, schema):
        self.schema = schema
        self.time_partitioning = None
        self.clustering_fields = []


def test_ensure_table_creates_when_missing(monkeypatch):
    client = MagicMock()
    client.project = "proj"
    created_table = DummyTable(schema=[])
    client.get_table.side_effect = Exception("not found")
    client.create_table.return_value = created_table

    table = ensure_table(client, "ds", "tbl")

    client.create_table.assert_called_once()
    assert table is created_table
    created = client.create_table.call_args[0][0]
    assert len(created.schema) == 10
    assert created.time_partitioning.field == "timestamp"
    assert created.clustering_fields == ["exchange", "symbol"]


def test_ensure_table_repairs_empty_schema(monkeypatch):
    client = MagicMock()
    client.project = "proj"
    empty_table = DummyTable(schema=[])
    repaired_table = DummyTable(schema=["timestamp"])
    client.get_table.return_value = empty_table
    client.update_table.return_value = repaired_table

    table = ensure_table(client, "ds", "tbl")

    client.update_table.assert_called_once()
    assert table is repaired_table
    args, kwargs = client.update_table.call_args
    assert args[1] == ["schema", "time_partitioning", "clustering_fields"]
    assert kwargs == {}


def test_insert_rows_ensures_schema_once(monkeypatch):
    client = MagicMock()
    client.project = "proj"
    existing_table = DummyTable(schema=["timestamp"])
    client.get_table.return_value = existing_table
    client.insert_rows_json.return_value = []

    # isolate global cache
    monkeypatch.setattr(storage, "_ensured_tables", set())

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

    insert_rows(client, "ds", "tbl", [record])
    insert_rows(client, "ds", "tbl", [record])

    # ensure_table should have been invoked only once per table id
    assert client.get_table.call_count == 1
    assert client.insert_rows_json.call_count == 2

