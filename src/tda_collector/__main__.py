import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery

from tda_collector import adapter
from tda_collector.config import load_config
from tda_collector.logging_util import build_logger, env_labels, log_struct
from tda_collector.scheduler import run_history_loop, run_live_loop
from tda_collector.storage import ensure_table


def parse_args():
    parser = argparse.ArgumentParser(description="TDA Large Collector")
    parser.add_argument("--mode", choices=["live", "history"], default="live")
    parser.add_argument("--config", default=os.environ.get("CONFIG_PATH", "./config.yaml"))
    parser.add_argument("--start", help="ISO8601 start for history mode")
    parser.add_argument("--end", help="ISO8601 end for history mode (optional)")
    parser.add_argument("--dataset", default=os.environ.get("BQ_DATASET", "crypto"))
    parser.add_argument("--table", default=os.environ.get("BQ_TABLE", "market_data_ohlcv"))
    parser.add_argument("--backoff-base", type=float, default=None)
    parser.add_argument("--backoff-factor", type=float, default=None)
    parser.add_argument("--backoff-max", type=float, default=None)
    parser.add_argument("--backoff-attempts", type=int, default=None)
    return parser.parse_args()


def main():
    # Local convenience: load .env if present (noop in docker if not provided)
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)

    args = parse_args()
    cfg = load_config(args.config)
    logger = build_logger(
        service_name=env_labels()["service_name"],
        environment=env_labels()["environment"],
        loki_url=os.environ.get("LOKI_URL") or os.environ.get("LOKI_ENDPOINT"),
        loki_username=os.environ.get("LOKI_USERNAME"),
        loki_password=os.environ.get("LOKI_PASSWORD"),
    )

    bq_client = bigquery.Client()
    ensure_table(bq_client, args.dataset, args.table)

    tasks_live = []
    tasks_history = []
    for ex_name, pairs in cfg.exchanges.items():
        client = adapter.build_client(ex_name)
        for pair in pairs:
            for tf in pair.timeframes:
                tasks_live.append((client, pair.symbol, tf))
                if args.mode == "history":
                    start_iso = args.start
                    end_iso = args.end or datetime.now(tz=timezone.utc).isoformat()
                    start_ms = int(datetime.fromisoformat(start_iso).timestamp() * 1000)
                    end_ms = int(datetime.fromisoformat(end_iso).timestamp() * 1000)
                    tasks_history.append((client, pair.symbol, tf, start_ms, end_ms))

    log_struct(logger, {**env_labels(), "mode": args.mode}, {"event": "config_loaded"})

    backoff_cfg = {
        "base_delay": args.backoff_base or cfg.settings.backoff_base,
        "factor": args.backoff_factor or cfg.settings.backoff_factor,
        "max_delay": args.backoff_max or cfg.settings.backoff_max,
        "max_attempts": args.backoff_attempts or cfg.settings.backoff_attempts,
    }

    if args.mode == "live":
        run_live_loop(
            cfg.settings.update_interval_seconds,
            tasks_live,
            logger=logger,
            bq_client=bq_client,
            dataset=args.dataset,
            table=args.table,
            backoff_cfg=backoff_cfg,
        )
    else:
        run_history_loop(
            tasks_history,
            logger=logger,
            bq_client=bq_client,
            dataset=args.dataset,
            table=args.table,
            backoff_cfg=backoff_cfg,
        )


if __name__ == "__main__":
    main()

