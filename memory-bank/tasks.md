# Tasks

## Status: REFLECT Complete (Level 4 – Complex System)

### Task Definition
**Project**: TDA Large Collector - Cryptocurrency Market Data Ingestion Microservice  
**Task**: Implement complete Python microservice system per SDD v1.0.0

### Complexity Determination (from VAN)
- **Scope**: System-wide (ingestion, storage, logging, scheduling, containerization)  
- **Design Decisions**: Complex (architecture, data model, reliability, infra)  
- **Risk**: High (external APIs, cloud services, data integrity, production stability)  
- **Effort**: High (multi-week, comprehensive testing)  
- **Keywords**: system, microservice, architecture, integration, framework  
- **Result**: **Level 4 - Complex System**

### System & Component Breakdown
- **Core runtime**: Python 3.13 (slim) container
- **Config & CLI**: YAML loader, env overrides, mode flags (live/history)
- **Exchange adapters**: ccxt REST client (enableRateLimit, retries/backoff)
- **Scheduler**: live loop (interval), history pagination loop (date range)
- **Data model**: OHLCV normalization, BQ schema (partition on timestamp; cluster by exchange/symbol)
- **Storage**: BigQuery client (insert_rows_json streaming), idempotent table create
- **Logging/Telemetry**: Console + Grafana Loki (service/env/exchange tags)
- **Resilience**: backoff on NetworkError, rate-limit handling, error logging without crash
- **Packaging**: Dockerfile, requirements, entrypoints
- **Testing**: pytest with mocks for ccxt and bigquery; required cases per SDD

### Technology Stack (initial)
- Language: Python 3.13
- Libraries: ccxt, google-cloud-bigquery, python-logging-loki (or HTTP handler), pydantic/yaml loader, schedule/time
- Tooling: pytest, unittest.mock, docker, makefile (optional)

### Technology Validation Checkpoints
- [x] Project scaffolding command decided → **pip + requirements.txt** (add requirements-dev.txt if needed)
- [x] Minimal “hello world” plan → script to import ccxt (no network), instantiate mocked `google.cloud.bigquery.Client` with env `GOOGLE_APPLICATION_CREDENTIALS`, emit Loki-shaped JSON to stdout
- [x] Logging shape validated → Labels: `service_name`, `environment`, `exchange`, `mode`, `timeframe`, `symbol`, `level`; Fields: `event`, `message`, `duration_ms`, `attempt`, `batch_size`, `rows`, `status`
- [x] Docker build plan validated → Base `python:3.13-slim`; create non-root user; copy requirements & install; copy src/config; entrypoint `python -m tda_collector --mode=live`
- [x] Test runner baseline → `pytest -q` discovery with mocks for ccxt/BQ; no real network

### Dependency Pinning (initial)
- Runtime: `ccxt`, `google-cloud-bigquery`, `python-logging-loki` (or requests-based sender), `PyYAML`, `pydantic` (or dataclasses), `schedule` (or `time` loop), `python-dateutil` (optional)
- Tooling/Test: `pytest`, `pytest-mock`, `types-PyYAML` (optional)
- Packaging: requirements.txt (pins); requirements-dev.txt for test-only deps

### Docker Plan (ready)
- Base: `python:3.13-slim`
- Steps: add non-root user; apt-get minimal build deps; copy requirements*; `pip install --no-cache-dir -r requirements.txt`; copy `src/` and `config.yaml`; `ENV CONFIG_PATH=/app/config.yaml`; `ENTRYPOINT ["python", "-m", "tda_collector"]`

### Minimal QA POC (design)
- Import ccxt (no network), build BigQuery Client with dummy project + env creds path (mocked file), log Loki-shaped JSON to stdout, ensure `pytest -q` runs a dummy test using `unittest.mock` for ccxt/BQ

### Implementation Plan (phased)
1) **Scaffolding & Tooling**
   - Repo layout (`src/`, `tests/`, `config.yaml`, `Dockerfile`, `Makefile` optional)
   - Requirements/lock; basic `__main__` entry and CLI args (`--mode`, `--start`, `--end`)
2) **Configuration & Models**
   - YAML loader with validation (symbols/timeframes, update_interval_seconds)
   - Dataclasses/pydantic models for config and OHLCV row mapping to BQ schema
3) **Exchange Adapter Layer**
   - ccxt client factory (enableRateLimit, retries/backoff for NetworkError)
   - Live fetch: last 2 bars logic (previous closed + current open)
   - History fetch: paginated loop until end range
4) **Storage Layer**
   - BigQuery table ensure/create (partition, cluster)
   - Payload builder matching schema; streaming inserts with error handling
5) **Logging/Telemetry**
   - Structured logger with Loki handler + stdout; required tags (service_name, environment, exchange, level)
6) **Scheduler / Orchestration**
   - Live loop using interval with graceful sleep and per-exchange iteration
   - History runner with date windowing and exit code 0 on completion
7) **Error Handling & Resilience**
   - Exponential backoff for ccxt.NetworkError; respect RateLimitExceeded
   - Non-fatal logging; retries on next cycle
8) **Testing**
   - pytest + mocks (ccxt, bigquery)
   - Required tests: config loader, fetch_ohlcv_live logic, bigquery insert payload, history pagination
9) **Packaging & Delivery**
   - Dockerfile (slim Python 3.13), entrypoint script, runtime env var wiring
   - README updates per SDD (setup, config example, env vars, commands, tests)

### Creative Phases Required (to run in CREATIVE mode)
- [ ] Architecture diagram & component responsibilities
- [ ] Data model finalization (BQ schema validation & payload mapping)
- [ ] Resilience/backoff strategy tuning
- [ ] Logging taxonomy (Loki labels/fields)

### Dependencies / External
- Google BigQuery (service account key via GOOGLE_APPLICATION_CREDENTIALS)
- Grafana Loki endpoint/creds
- Exchange REST endpoints via ccxt (mocked in tests; rate limits considered)

### Risks & Mitigations
- **Rate limits / API instability**: use ccxt rate limiter + backoff; cap concurrency.
- **BigQuery write errors**: validate schema and payload, batch size control, log failures.
- **Clock/skew/timeframe issues**: use exchange time and ISO8601 handling; unit tests for boundaries.
- **Docker image bloat**: use slim base, pin deps, multi-stage if needed.

### Milestones (draft)
- M1: Scaffolding + config/model layer ready
- M2: Adapter + live/history logic implemented
- M3: BigQuery + logging integration in place
- M4: Tests passing and Docker build succeeds
- M5: Documentation (README) complete

### Mode Routing
- PLAN (this document) → CREATIVE (for design decisions) → VAN QA → BUILD → REFLECT → ARCHIVE

---

## Reflection (BigQuery schema hotfix)
- Status: Reflection recorded in `memory-bank/reflection/reflection-bq-schema.md`
- What went well: Fast unit-test harness around ensure/insert; clear schema reference.
- Challenges: Existing partitioning/clustering prevented naive PATCH; no Loki logs when crash occurred pre-loop.
- Lessons: Update only missing fields on existing BQ tables; guard inserts with one-time ensure; emit early breadcrumbs before storage init.
- Next steps: Add optional `bq_ensure_table` log; consider admin CLI for safe schema repair.

## Reflection (history page limit doc)
- Status: Reflection recorded in `memory-bank/reflection/reflection-history-page-limit.md`
- Scope: Documented that `history_page_limit` caps candles per request and pagination continues until the interval is fully fetched.

## Archive (history page limit doc)
- Status: Archived in `memory-bank/archive/archive-history-page-limit.md`
- Notes: README/config updated; pagination behavior clarified for history mode.

## Creative Decisions (Architecture, Data, Resilience, Logging)

📌 CREATIVE PHASE: Architecture & Data Model
--------------------------------------------
1️⃣ PROBLEM  
- Need clear component boundaries for ccxt polling, BQ writes, and telemetry; must support live loop and history pagination with BigQuery schema guarantee.

2️⃣ OPTIONS (summary)  
- A: Monolith process with layered modules (config, scheduler, fetcher, storage, logging).  
- B: Split into multiple processes (fetcher + writer) coordinated externally.  
- C: Event-driven queue between fetch and write.

3️⃣ DECISION  
- Select A: Single-process layered microservice with clear module boundaries; simplest deployment, minimal infra, matches SDD scope.

4️⃣ IMPLEMENTATION NOTES  
- Modules: config loader, cli/mode dispatcher, scheduler (live interval + history window iterator), exchange adapter (ccxt), transformer (OHLCV normalize), storage (BQ ensure/create + streaming insert), logging (Loki + stdout), resilience utilities (backoff).  
- Entrypoints: `--mode=live|history`, `--start`, `--end`, `--config`.  
- Threading not required; sequential per-exchange loop with rate-limit respect.

📌 CREATIVE PHASE: BigQuery Data Model
--------------------------------------
- Table: `market_data_ohlcv` (partition by DATE(timestamp), cluster by exchange, symbol).  
- Schema: timestamp (TIMESTAMP), exchange (STRING), symbol (STRING), timeframe (STRING), open/high/low/close (FLOAT), volume (FLOAT), ingested_at (TIMESTAMP).  
- Insert shape: use ISO8601/UTC; ensure timestamps from exchange ms.  
- Idempotence: rely on upstream unique (timestamp, exchange, symbol, timeframe); no dedupe in Phase 1.

📌 CREATIVE PHASE: Resilience / Backoff
---------------------------------------
- ccxt.NetworkError: exponential backoff with jitter, base 1s, factor 2, max 32s, max 5 attempts per call; log warn, skip to next cycle on failure.  
- RateLimitExceeded: rely on ccxt `enableRateLimit=True`; if raised, sleep suggested delay or backoff base 2s (cap 30s).  
- History pagination: store `since` cursor per request; on failure, retry page with backoff; on repeated failure, log error and continue to next symbol to avoid stall.  
- Live loop guard: ensure minimum sleep interval even after errors.

📌 CREATIVE PHASE: Logging Taxonomy (Loki + stdout)
---------------------------------------------------
- Required labels/tags: `service_name`, `environment`, `exchange`, `level`, `mode` (live|history), `timeframe`, `symbol` (where available).  
- Structured fields: event, message, error, duration_ms, attempt, batch_size, rows, status.  
- Key events: config_loaded, loop_tick, fetch_start/ok/error, bq_ensure_table, bq_insert_ok/error, backoff_retry, history_page_done, history_complete, live_cycle_complete.  
- Formatter: JSON lines for stdout; Loki HTTP handler mirrors fields.

✅ Creative verification: problem defined, options considered, decisions recorded, implementation guidance captured.

### Artifacts
- Architecture diagrams: `memory-bank/creative/creative-architecture.md`

