# Bug Fix Reflection: History ISO8601 Z parsing and pagination bounds

## Summary
History mode now accepts `Z`-suffixed ISO8601 inputs and restricts pagination to the requested window so only the expected candles are inserted.

## Issue
History runs rejected `Z` timestamps and, after parsing fix, continued logging pages beyond `end` and inserted zero-row page logs.

## Root Cause
- CLI parsing used `datetime.fromisoformat` without normalizing `Z`.
- History loop advanced cursor with a fixed 60s step and logged even when no rows were inserted, so it could overshoot the requested window and emit empty logs.

## Solution
- Normalize `Z` to `+00:00` and default naive timestamps to UTC.
- In `run_history_loop`, derive step from `client.parse_timeframe`, filter rows to `[start_ms, end_ms)`, insert only bounded rows, and skip logging when nothing is inserted; stop when the page is entirely beyond `end_ms`.

## Files Changed
- `src/tda_collector/__main__.py`
- `src/tda_collector/scheduler.py`

## Verification
- Manual run: `--mode=history --start=2025-03-01T00:00:00Z --end=2025-04-01T00:00:00Z` returns one 1M candle and emits a single `history_page_done` log with `rows=1`; no zero-row logs.

## Additional Notes
- Cursor advancement now respects exchange timeframe parsing; fallback remains 60s if parsing is unavailable.

