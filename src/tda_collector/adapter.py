from datetime import datetime, timezone
from typing import Any, List, Tuple

import ccxt

from tda_collector.models import OHLCVRecord


def build_client(exchange_id: str) -> ccxt.Exchange:
    cls = getattr(ccxt, exchange_id)
    return cls({"enableRateLimit": True})


def fetch_last_two(
    client: ccxt.Exchange,
    symbol: str,
    timeframe: str,
) -> Tuple[OHLCVRecord, OHLCVRecord]:
    candles: List[List[Any]] = client.fetch_ohlcv(symbol, timeframe=timeframe, limit=2)
    if len(candles) < 2:
        raise ValueError("Not enough candles returned")
    prev, current = candles[-2], candles[-1]
    return _to_record(client.id, symbol, timeframe, prev), _to_record(
        client.id, symbol, timeframe, current
    )


def fetch_history_page(
    client: ccxt.Exchange,
    symbol: str,
    timeframe: str,
    since_ms: int,
    limit: int = 200,
) -> List[OHLCVRecord]:
    candles: List[List[Any]] = client.fetch_ohlcv(
        symbol, timeframe=timeframe, since=since_ms, limit=limit
    )
    return [_to_record(client.id, symbol, timeframe, c) for c in candles]


def _to_record(
    exchange: str, symbol: str, timeframe: str, candle: List[Any]
) -> OHLCVRecord:
    ts_ms, o, h, l, c, v = candle
    ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return OHLCVRecord(
        timestamp=ts,
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        open=float(o),
        high=float(h),
        low=float(l),
        close=float(c),
        volume=float(v),
        ingested_at=datetime.now(tz=timezone.utc),
    )

