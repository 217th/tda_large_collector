# TASK ARCHIVE: History Page Limit Documentation

## METADATA
- Task ID: history-page-limit-doc
- Date: 2025-12-10
- Complexity: Level 2 – Simple Enhancement (documentation)
- Related Mode: HISTORY pagination

## SUMMARY
- Documented the global `history_page_limit` setting as the per-request candle cap in history mode and clarified that the scheduler issues multiple sequential requests until the full interval is covered when more data is available.

## REQUIREMENTS
- Make the history pagination limit configurable at a global level in config.
- Explain behavior when the interval contains more candles than a single request limit.

## IMPLEMENTATION
- Added `history_page_limit` to config examples and described its effect in README.
- Noted pagination behavior: multiple back-to-back requests until the interval is fully fetched.
- Sample config updated to Bybit symbols while retaining the new setting.

## TESTING
- `pytest` (all suites) — passed.

## LESSONS LEARNED
- Pairing configuration knobs with precise pagination semantics reduces ambiguity for exchanges with strict page caps or long intervals.

## REFERENCES
- Reflection: `memory-bank/reflection/reflection-history-page-limit.md`
- Code/Docs: `README.md`, `config.yaml`

