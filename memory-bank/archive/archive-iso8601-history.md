# TASK ARCHIVE: History ISO8601 Z parsing and windowing

## METADATA
- Task ID: iso8601-history
- Date: 2025-12-10
- Complexity: Level 1 (Quick Bug Fix)
- Mode Path: VAN → BUILD → REFLECT → ARCHIVE

## SUMMARY
Fixed history mode to accept `Z`-suffixed ISO8601 inputs and to paginate strictly within the requested time window, avoiding extra candles and zero-row page logs.

## REQUIREMENTS
- Accept `--start/--end` with `Z` suffix.
- Insert only candles within `[start_ms, end_ms)`.
- Avoid logging “inserted page” when nothing is stored.

## IMPLEMENTATION
- Normalized `Z` to `+00:00`; defaulted naive timestamps to UTC in CLI parsing.
- History loop now derives step from `client.parse_timeframe`, filters rows to the requested window, inserts only bounded rows, skips logging when no rows inserted, and stops if a page is entirely beyond `end_ms`.
- Files: `src/tda_collector/__main__.py`, `src/tda_collector/scheduler.py`.

## TESTING
- Manual run: `python -m tda_collector --mode=history --config=./config.yaml --start=2025-03-01T00:00:00Z --end=2025-04-01T00:00:00Z`  
  - Result: one 1M candle inserted; single `history_page_done` log with `rows=1`; no zero-row logs.

## LESSONS LEARNED
- Normalize `Z` early; treat naive timestamps as UTC for CLI convenience.
- History pagination should advance by timeframe, not fixed 60s, and must guard against empty-page logging.

## REFERENCES
- Reflection: `memory-bank/reflection/reflection-iso8601-history.md`
- Tasks: `memory-bank/tasks.md`

