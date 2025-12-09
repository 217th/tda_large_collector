# Reflection – Loki logging fix (Level 1 bugfix)

## Summary
- Fixed Loki logging failures: initial 405 (wrong endpoint shape), then 401 (env precedence), then 400 (stale timestamp in debug probe).
- Changes: normalize push URL with `/loki/api/v1/push`, env cleaning, `.env` override=True, optional debug probe (`LOKI_DEBUG=1`) and TLS toggle (`LOKI_INSECURE=1`), debug probe now uses current `time_ns`.

## What went well
- Reused working sample (temp/sandbox_loki_logging) to align expectations (base URL, auth).
- Added lightweight debug hook to surface status/body without crashing main flow.

## Challenges
- Mixed env precedence: existing shell vars shadowed `.env` until `override=True`.
- Loki push URLs vary (stack vs regional); needed normalization instead of assuming suffix presence.
- Debug probe originally sent epoch-ish timestamp, triggering “too old” 400.

## Lessons learned
- Always strip env values (export/quotes/spaces) before auth.
- For external sinks, log the exact push URL and user preview during debug; fail soft.
- Use real-time timestamps for any health/debug push to Loki.

## Process/tech improvements
- Keep `LOKI_DEBUG` path for future incidents; consider structured startup health check.
- Document that `.env` overrides environment and expects base URL only.
- Consider unit test or smoke script to exercise Loki handler with fake responses.

