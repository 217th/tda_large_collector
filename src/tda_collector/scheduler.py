import time
from typing import Callable, Iterable, Tuple

from tda_collector.adapter import fetch_last_two, fetch_history_page
from tda_collector.logging_util import log_struct, env_labels
from tda_collector.storage import insert_rows
from tda_collector.resilience import retry_with_backoff


def run_live_loop(
    interval_seconds: int,
    tasks: Iterable[Tuple],
    fetch_fn: Callable = fetch_last_two,
    storage_fn: Callable = insert_rows,
    logger=None,
    bq_client=None,
    dataset="crypto",
    table="market_data_ohlcv",
    backoff_cfg=None,
):
    labels = {**env_labels(), "mode": "live"}
    backoff_cfg = backoff_cfg or {}
    while True:
        for client, symbol, timeframe in tasks:
            try:
                prev_bar, curr_bar = retry_with_backoff(
                    fetch_fn, (client, symbol, timeframe), **backoff_cfg
                )
                retry_with_backoff(
                    storage_fn, (bq_client, dataset, table, [prev_bar, curr_bar]), **backoff_cfg
                )
                log_struct(
                    logger,
                    {**labels, "exchange": client.id, "symbol": symbol, "timeframe": timeframe},
                    {"event": "live_cycle_complete", "message": "live insert ok"},
                )
            except Exception as exc:  # pragma: no cover - runtime guard
                log_struct(
                    logger,
                    {**labels, "exchange": getattr(client, "id", None), "symbol": symbol, "timeframe": timeframe},
                    {"event": "live_cycle_error", "error": str(exc)},
                )
        time.sleep(interval_seconds)


def run_history_loop(
    tasks: Iterable[Tuple],
    fetch_page_fn: Callable = fetch_history_page,
    storage_fn: Callable = insert_rows,
    logger=None,
    bq_client=None,
    dataset="crypto",
    table="market_data_ohlcv",
    timeframe_window_ms: int = 60_000,
    backoff_cfg=None,
):
    labels = {**env_labels(), "mode": "history"}
    backoff_cfg = backoff_cfg or {}
    for client, symbol, timeframe, start_ms, end_ms in tasks:
        # Derive step from exchange timeframe parsing when available; fallback to provided window.
        step_ms = timeframe_window_ms
        if hasattr(client, "parse_timeframe"):
            try:
                step_ms = int(client.parse_timeframe(timeframe) * 1000)
            except Exception:
                step_ms = timeframe_window_ms

        cursor = start_ms
        while cursor < end_ms:
            try:
                rows = retry_with_backoff(
                    fetch_page_fn, (client, symbol, timeframe, cursor), **backoff_cfg
                )
                if not rows:
                    break
                # Keep only candles inside the requested window.
                bounded_rows = [
                    row for row in rows if cursor <= int(row.timestamp.timestamp() * 1000) < end_ms
                ]
                if bounded_rows:
                    retry_with_backoff(
                        storage_fn, (bq_client, dataset, table, bounded_rows), **backoff_cfg
                    )
                    cursor = int(bounded_rows[-1].timestamp.timestamp() * 1000 + step_ms)
                    log_struct(
                        logger,
                        {**labels, "exchange": client.id, "symbol": symbol, "timeframe": timeframe},
                        {
                            "event": "history_page_done",
                            "message": "inserted page",
                            "rows": len(bounded_rows),
                            "cursor_ms": cursor,
                        },
                    )
                else:
                    # No rows inside the requested window; advance cursor using the fetched page.
                    first_ms = int(rows[0].timestamp.timestamp() * 1000)
                    last_ms = int(rows[-1].timestamp.timestamp() * 1000)
                    cursor = int(last_ms + step_ms)
                    if first_ms >= end_ms:
                        break

                if cursor >= end_ms:
                    break
            except Exception as exc:  # pragma: no cover - runtime guard
                log_struct(
                    logger,
                    {**labels, "exchange": getattr(client, "id", None), "symbol": symbol, "timeframe": timeframe},
                    {"event": "history_error", "error": str(exc)},
                )
                break
    log_struct(logger, labels, {"event": "history_complete", "message": "history mode finished"})

