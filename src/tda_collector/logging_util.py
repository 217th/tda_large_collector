import json
import logging
import os
import time
from typing import Any, Dict, Optional

try:
    from logging_loki import LokiHandler
except ImportError:  # pragma: no cover - optional handler
    LokiHandler = None  # type: ignore

try:  # used only for optional debug check
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional dependency comes with logging_loki
    requests = None  # type: ignore


def build_logger(
    service_name: str,
    environment: str,
    level: str = "INFO",
    loki_url: Optional[str] = None,
    loki_username: Optional[str] = None,
    loki_password: Optional[str] = None,
) -> logging.Logger:
    def _parse_env_bool(value: Optional[str]) -> bool:
        if value is None:
            return False
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    def _env_clean(raw: Optional[str]) -> Optional[str]:
        """Strip export/quotes/whitespace from env values to avoid auth errors."""
        if raw is None:
            return None
        cleaned = raw.strip()
        if cleaned.lower().startswith("export "):
            cleaned = cleaned[7:].strip()
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()
        return cleaned or None

    def _normalize_loki_url(raw: Optional[str]) -> Optional[str]:
        """Ensure the Loki push URL includes the expected /loki/api/v1/push suffix."""
        if not raw:
            return None
        cleaned = raw.strip()
        if not cleaned:
            return None
        lowered = cleaned.lower()
        if "/loki/api/" in lowered or "/api/prom/push" in lowered:
            return cleaned
        return cleaned.rstrip("/") + "/loki/api/v1/push"

    def _maybe_debug_request(url: str, username: str, password: str, verify_tls: bool) -> None:
        """
        Optional one-off request to help pinpoint 401s. Controlled by LOKI_DEBUG=1.
        Does not raise to avoid crashing the service; prints to stderr.
        """
        if not requests or not _parse_env_bool(os.environ.get("LOKI_DEBUG")):
            return
        try:
            now_ns = time.time_ns()
            resp = requests.post(
                url,
                auth=(username, password),
                json={
                    "streams": [
                        {
                            "stream": {"app": "tda-collector"},
                            "values": [[str(now_ns), "debug_ping"]],
                        }
                    ]
                },
                verify=verify_tls,
                timeout=5,
            )
            if resp.status_code != 204:
                preview_user = username[:4] + "…" if len(username) > 4 else username
                print(
                    f"[loki-debug] status={resp.status_code} body={resp.text!r} url={url} user={preview_user} verify_tls={verify_tls}",
                    file=os.sys.stderr,
                )
        except Exception as exc:  # pragma: no cover - debug path
            print(f"[loki-debug] request failed: {exc}", file=os.sys.stderr)

    logger = logging.getLogger(service_name)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter("%(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(stream_handler)

    normalized_loki_url = _normalize_loki_url(_env_clean(loki_url))
    clean_username = _env_clean(loki_username) or ""
    clean_password = _env_clean(loki_password) or ""
    verify_tls = not _parse_env_bool(os.environ.get("LOKI_INSECURE"))

    if normalized_loki_url and LokiHandler:
        _maybe_debug_request(normalized_loki_url, clean_username, clean_password, verify_tls)
        loki_handler = LokiHandler(
            url=normalized_loki_url,
            auth=(clean_username, clean_password),
            version="1",
            tags={"service": service_name, "environment": environment},
        )
        loki_handler.setFormatter(formatter)
        try:
            loki_handler.emitter.session.verify = verify_tls
        except Exception:
            pass
        logger.addHandler(loki_handler)

    logger.propagate = False
    return logger


def log_struct(
    logger: logging.Logger,
    labels: Dict[str, Any],
    fields: Dict[str, Any],
) -> None:
    record = {**fields, **{f"label_{k}": v for k, v in labels.items() if v is not None}}
    logger.info(json.dumps(record))


def env_labels() -> Dict[str, str]:
    return {
        "service_name": os.environ.get("SERVICE_NAME", "tda-collector"),
        "environment": os.environ.get("ENVIRONMENT", "dev"),
    }

