import os
from pathlib import Path
from typing import Dict, List

import yaml

from tda_collector.models import Config, Settings, ExchangePair


def load_config(path: str) -> Config:
    cfg_path = Path(path or os.environ.get("CONFIG_PATH", "./config.yaml"))
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found at {cfg_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    settings_data = data.get("settings", {}) or {}
    exchanges_data: Dict[str, List[Dict]] = data.get("exchanges", {}) or {}

    settings = Settings(
        update_interval_seconds=int(settings_data.get("update_interval_seconds", 60)),
        backoff_base=float(settings_data.get("backoff_base", 1.0)),
        backoff_factor=float(settings_data.get("backoff_factor", 2.0)),
        backoff_max=float(settings_data.get("backoff_max", 32.0)),
        backoff_attempts=int(settings_data.get("backoff_attempts", 5)),
    )

    exchanges: Dict[str, List[ExchangePair]] = {}
    for ex_name, pairs in exchanges_data.items():
        ex_pairs: List[ExchangePair] = []
        if not pairs:
            continue
        for pair in pairs:
            ex_pairs.append(
                ExchangePair(
                    symbol=str(pair["symbol"]),
                    timeframes=[str(tf) for tf in pair.get("timeframes", [])],
                )
            )
        exchanges[ex_name] = ex_pairs

    return Config(settings=settings, exchanges=exchanges)

