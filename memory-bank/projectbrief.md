# Project Brief

## Project: TDA Large Collector

### Overview
A Python-based microservice for ingesting cryptocurrency market data (OHLCV) from multiple exchanges via the `ccxt` library. Data is stored in Google BigQuery for analytical purposes. The service operates in a containerized environment with support for both continuous scheduled collection (LIVE mode) and ad-hoc historical backfilling (HISTORY mode).

### Key Requirements
- Multi-exchange support via `ccxt` library
- Configurable target pairs (Symbols) and timeframes
- Data persistence to Google BigQuery
- Remote logging to Grafana Loki
- Dual-mode operation: LIVE (Scheduled) and HISTORY (One-off backfill)
- Docker containerization
- Comprehensive automated testing

### Technology Stack
- **Runtime**: Python 3.13 (Slim Docker Image)
- **Market Data**: `ccxt` (Latest stable)
- **Storage**: `google-cloud-bigquery`
- **Logging**: `python-logging-loki` or standard `logging` with HTTP handler
- **Scheduling**: `schedule` library or `time.sleep` loop

### Status
- **Documentation**: System Design Document (SDD) v1.0.0 - CONFIRMED
- **Implementation**: Not started
- **Complexity Level**: Level 4 - Complex System

