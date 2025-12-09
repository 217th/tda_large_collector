from typing import List, Set

from google.cloud import bigquery

from tda_collector.models import OHLCVRecord


_ensured_tables: Set[str] = set()


def ensure_table(client: bigquery.Client, dataset: str, table: str) -> bigquery.Table:
    table_id = f"{client.project}.{dataset}.{table}"
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("exchange", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timeframe", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("open", "FLOAT"),
        bigquery.SchemaField("high", "FLOAT"),
        bigquery.SchemaField("low", "FLOAT"),
        bigquery.SchemaField("close", "FLOAT"),
        bigquery.SchemaField("volume", "FLOAT"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ]

    table_obj = bigquery.Table(table_id, schema=schema)
    table_obj.time_partitioning = bigquery.TimePartitioning(field="timestamp")
    table_obj.clustering_fields = ["exchange", "symbol"]

    try:  # Attempt to reuse existing table if it already exists
        table_obj = client.get_table(table_id)
    except Exception:
        return client.create_table(table_obj)

    # If a table exists but has no schema (e.g., created incorrectly), repair it
    if not table_obj.schema:
        fields_to_update = ["schema"]
        table_obj.schema = schema

        # Only set partitioning/clustering if missing to avoid BQ PATCH errors
        if not table_obj.time_partitioning:
            table_obj.time_partitioning = bigquery.TimePartitioning(field="timestamp")
            fields_to_update.append("time_partitioning")
        if not table_obj.clustering_fields:
            table_obj.clustering_fields = ["exchange", "symbol"]
            fields_to_update.append("clustering_fields")

        return client.update_table(table_obj, fields_to_update)
    return table_obj


def insert_rows(client: bigquery.Client, dataset: str, table: str, rows: List[OHLCVRecord]) -> None:
    table_id = f"{client.project}.{dataset}.{table}"

    # Ensure schema exists once per table to avoid "no schema" errors in streaming inserts
    if table_id not in _ensured_tables:
        ensure_table(client, dataset, table)
        _ensured_tables.add(table_id)

    payload = [r.to_bq_row() for r in rows]
    errors = client.insert_rows_json(table_id, payload)
    if errors:
        raise RuntimeError(f"Failed to insert rows: {errors}")

