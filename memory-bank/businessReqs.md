**STATUS: CONFIRMED**
**DOCUMENT TYPE:** SYSTEM DESIGN DOCUMENT (SDD)
**VERSION:** 1.0.0

-----

## 1\. Introduction

### 1.1 Purpose

The purpose of this document is to define the technical specifications for a Python-based microservice designed to ingest cryptocurrency market data (OHLCV) from various exchanges via the `ccxt` library. The data will be stored in Google BigQuery for analytical purposes. The service operates in a containerized environment with support for both continuous scheduled collection and ad-hoc historical backfilling.

### 1.2 Scope

  * **In Scope:**
      * Integration with `ccxt` for multi-exchange support.
      * Configurable target pairs (Symbols) and timeframes.
      * Data persistence to Google BigQuery.
      * Remote logging to Grafana Loki.
      * Dual-mode operation: `LIVE` (Scheduled) and `HISTORY` (One-off).
  * **Out of Scope:**
      * Data deduplication (postponed to Phase 2).
      * Real-time websocket streaming (REST API polling is sufficient).
      * Complex data transformation beyond standard OHLCV mapping.

-----

## 2\. System Architecture

### 2.1 High-Level Design

The system functions as a standalone Python process encapsulated in a Docker container. It reads configuration from a YAML file and secrets from Environment Variables.

**Data Flow:**

1.  **Input:** Configuration (YAML) defines `Exchange -> Symbol -> Timeframe`.
2.  **Process:** Python Application polls `ccxt` REST endpoints.
3.  **Output:** Rows are inserted into a Partitioned BigQuery Table.
4.  **Telemetry:** Logs (Info/Error) are pushed to Grafana Loki via HTTP.

### 2.2 Technology Stack

  * **Runtime:** Python 3.13 (Slim Docker Image).
  * **Market Data Adapter:** `ccxt` (Latest stable).
  * **Storage Driver:** `google-cloud-bigquery`.
  * **Logging:** `python-logging-loki` (or standard `logging` with HTTP handler).
  * **Scheduling:** `schedule` library or simple `time.sleep` loop (internal to the Python process to ensure container autonomy).

-----

## 3\. Functional Requirements

### 3.1 Configuration Management

The system must parse a YAML configuration file (`config.yaml`).

  * **Requirement:** The file must be hot-swappable (via volume mount), though the application may require a restart to apply changes.
  * **Structure:**
    ```yaml
    settings:
      update_interval_seconds: 60  # Global polling rate for LIVE mode

    exchanges:
      binance:
        - symbol: "BTC/USDT"
          timeframes: ["1m", "1h", "1d"]
        - symbol: "ETH/USDT"
          timeframes: ["1d"]
      kraken:
        - symbol: "SOL/USD"
          timeframes: ["4h"]
    ```

### 3.2 Operating Modes

#### Mode A: LIVE (Daemon)

  * **Trigger:** Default behavior or via flag `--mode=live`.
  * **Behavior:** The service runs an infinite loop. At every configured interval, it requests OHLCV data.
  * **Data Logic:**
      * Must fetch the **last 2 bars**:
        1.  **Previous Bar (Closed):** Returns Entry (Open), Exit (Close), Min (Low), Max (High), Volume.
        2.  **Current Bar (Open/Incomplete):** Returns Entry (Open), Last Price (Close), Min (Low), Max (High), Current Volume.
  * **Error Handling:** If an API call fails, log the error to Loki and retry in the next cycle. Do not crash the container.

#### Mode B: HISTORY (Backfill)

  * **Trigger:** Via flag `--mode=history`.
  * **Arguments:**
      * `--start`: ISO8601 Datetime (e.g., `2023-01-01T00:00:00`).
      * `--end`: ISO8601 Datetime (optional, defaults to now).
  * **Behavior:** Iterates through the configured pairs and fetches all candles within the range using `ccxt` pagination (loops until the range is covered).
  * **Termination:** Process exits with code 0 upon completion.

### 3.3 Data Storage (BigQuery)

  * **Target:** Single Table `market_data_ohlcv`.
  * **Authentication:** via `GOOGLE_APPLICATION_CREDENTIALS` JSON file path.
  * **Write Strategy:** Streaming Inserts (`client.insert_rows_json`) or Batch Load (Streaming preferred for Live).

### 3.4 Logging

  * **Target:** Grafana Loki (Grafana Cloud).
  * **Transports:**
      * Console (Stdout) for Docker logs.
      * Loki HTTP API.
  * **Required Tags:** `service_name`, `environment`, `exchange`, `level`.

-----

## 4\. Data Design

### 4.1 BigQuery Schema

The coding agent must ensure the table exists or create it if missing (Idempotent check).

| Field Name | Type | Description | Notes |
| :--- | :--- | :--- | :--- |
| `timestamp` | `TIMESTAMP` | Candle open time | **Partition Key** (Day) |
| `exchange` | `STRING` | Exchange ID (e.g., 'binance') | **Cluster Key** |
| `symbol` | `STRING` | Unified Pair (e.g., 'BTC/USDT') | **Cluster Key** |
| `timeframe` | `STRING` | Candle period (e.g., '1h') | |
| `open` | `FLOAT` | Opening price | |
| `high` | `FLOAT` | Highest price | |
| `low` | `FLOAT` | Lowest price | |
| `close` | `FLOAT` | Closing price | |
| `volume` | `FLOAT` | Volume | |
| `ingested_at`| `TIMESTAMP` | System insertion time | For audit |

-----

## 5\. Implementation Requirements for Coding Agent

### 5.1 Environment Variables

The code must utilize `os.environ` to access:

  * `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key.
  * `LOKI_URL`: Full endpoint URL.
  * `LOKI_USERNAME`: Grafana User ID.
  * `LOKI_PASSWORD`: Grafana API Key.
  * `CONFIG_PATH`: Path to config file (Default: `./config.yaml`).

### 5.2 Error Handling & Resilience

  * **Network Errors:** Implement exponential backoff for `ccxt.NetworkError`.
  * **Rate Limits:** Respect `ccxt.RateLimitExceeded`. Rely on `ccxt` built-in rate limiter (`enableRateLimit=True`).

### 5.3 Automated Testing Requirements

The coding agent **must** provide a `tests/` folder using `pytest`.

1.  **Mocking:** Strictly strictly forbid real network calls during tests. Use `unittest.mock` to mock `ccxt.Exchange` and `google.cloud.bigquery.Client`.
2.  **Required Test Cases:**
      * `test_config_loader`: Verify YAML parsing validity.
      * `test_fetch_ohlcv_live`: Mock `ccxt` return data and assert correct formatting of the "Previous" vs "Current" bar logic.
      * `test_bigquery_insert`: Mock BQ client and verify payload structure matches schema.
      * `test_history_loop`: Verify pagination logic works given a mock set of historical data.

### 5.4 Documentation Requirements (README.md)

The coding agent must generate a `README.md` containing:

  * **Setup:** How to build the Docker image.
  * **Configuration:** Example `config.yaml` snippet.
  * **Env Vars:** List of required secrets.
  * **Execution Examples:**
      * Command for Live Mode.
      * Command for History Mode.
  * **Testing:** Command to run the test suite.
