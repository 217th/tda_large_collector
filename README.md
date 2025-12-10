# TDA Large Collector

Python microservice that ingests OHLCV market data via `ccxt` and writes to Google BigQuery with logging to Grafana Loki. Supports live scheduled collection and historical backfill.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

For development:
```bash
pip install -r requirements-dev.txt
```

## Configuration

See `config.yaml`:
```yaml
settings:
  update_interval_seconds: 60
  backoff_base: 1.0
  backoff_factor: 2.0
  backoff_max: 32.0
  backoff_attempts: 5
  history_page_limit: 200

exchanges:
  bybit:
    - symbol: "BTCUSDT"
      timeframes: ["1w", "1d", "1h"]
  # bybit symbols: https://bybit-exchange.github.io/docs/v5/enum#symbol
```

`history_page_limit` — максимальное число свечей за один запрос в history mode; если в заданном интервале доступно больше записей, планировщик выполнит несколько последовательных запросов, пока не получит все доступные данные.

Environment variables (loaded from `.env` if present when running locally, or pass via Docker envs; `.env` values now override existing env to align with loki_push.py behavior):
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to BigQuery service account JSON
- `LOKI_URL` (or `LOKI_ENDPOINT`), `LOKI_USERNAME`, `LOKI_PASSWORD`: Loki endpoint (base URL only, e.g. `https://<stack>.grafana.net`; `/loki/api/v1/push` is appended automatically) and auth. Credentials should be plain values without wrapping quotes or `export ` prefix.
- `LOKI_INSECURE`: set `1` to skip TLS verification for Loki (testing only).
- `LOKI_DEBUG`: set `1` to send a one-off debug push at startup and print status/body on failure (helps investigate 401/4xx).
- `CONFIG_PATH`: Override config file path (default `./config.yaml`)
- `BQ_DATASET` / `BQ_TABLE`: Target dataset/table (defaults: `crypto` / `market_data_ohlcv`)
- `SERVICE_NAME`, `ENVIRONMENT`: Logging labels
- Backoff (can override config via CLI flags):  
  - `--backoff-base`, `--backoff-factor`, `--backoff-max`, `--backoff-attempts`

## Execution

Live mode (default):
```bash
python -m tda_collector --mode=live --config=./config.yaml
```

History mode:
```bash
python -m tda_collector --mode=history \
  --config=./config.yaml \
  --start=2023-01-01T00:00:00Z \
  --end=2023-01-02T00:00:00Z
```

## Docker

```bash
docker build -t tda-collector .
docker run --rm \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json \
  -e LOKI_URL=https://loki.example/api/prom/push \
  -e LOKI_USERNAME=user \
  -e LOKI_PASSWORD=token \
  -v $(pwd)/key.json:/app/key.json:ro \
  tda-collector --mode=live
```

> Note: Build the image in an environment where Docker/BuildKit is available (not provided in this execution environment).

## Testing

```bash
pytest -q
```

`pytest.ini` sets `pythonpath=src` for local runs.

## Loki logging events
- `config_loaded` — config parsed and task list built.
- `live_cycle_complete` — live cycle succeeded; includes `exchange`, `symbol`, `timeframe`, `message`.
- `live_cycle_error` — live cycle failed; includes `error` plus available labels (`exchange`, `symbol`, `timeframe`).
- `history_page_done` — history page ingested; includes `rows`, `exchange`, `symbol`, `timeframe`, `message`.
- `history_error` — history processing failed; includes `error` plus available labels.
- `history_complete` — history mode finished.
- `debug_ping` — one-off startup message when `LOKI_DEBUG=1`, to diagnose auth/endpoint issues.

Common labels: `service_name`, `environment`, and `mode` (live/history); market events also include `exchange`, `symbol`, `timeframe`.

## BigQuery table schema
- Table: `market_data_ohlcv`
- Partitioning: `DATE(timestamp)` (time-partitioned on `timestamp`)
- Clustering: `exchange`, `symbol`
- Fields:
  - `timestamp` (TIMESTAMP, REQUIRED)
  - `exchange` (STRING, REQUIRED)
  - `symbol` (STRING, REQUIRED)
  - `timeframe` (STRING, REQUIRED)
  - `open` (FLOAT)
  - `high` (FLOAT)
  - `low` (FLOAT)
  - `close` (FLOAT)
  - `volume` (FLOAT)
  - `ingested_at` (TIMESTAMP)

## Notes
- Live loop fetches last two bars per symbol/timeframe.
- History mode paginates until the requested range is covered.
- BigQuery table is ensured on start (partition by timestamp, cluster by exchange/symbol).
- Logs are structured JSON to stdout and Loki (if configured).

## Acknowledgment
Thanks to the authors of [cursor-memory-bank](https://github.com/vanzan01/cursor-memory-bank) for their work—their project helped accelerate this one.

