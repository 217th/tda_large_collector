## Summary
- Added global config knob `history_page_limit` describing per-request candle count for history mode and documented pagination behavior when more data exists within the interval.
- Updated README config example (now Bybit sample) and clarified that the scheduler issues multiple sequential requests until the interval is covered.

## What Went Well
- Change was localized to documentation; behavior already enforced in code via settings wiring.
- Tests remained green, providing confidence in existing pagination logic.

## Challenges
- Minimal; only needed to keep README sample consistent with current config defaults.

## Lessons Learned
- Documenting pagination semantics alongside config knobs reduces ambiguity when exchanges cap page sizes or when intervals span large ranges.

## Next Steps
- Consider exposing per-exchange overrides if future APIs differ in max page sizes, while retaining the global default.

