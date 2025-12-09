from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Settings:
    update_interval_seconds: int = 60
    backoff_base: float = 1.0
    backoff_factor: float = 2.0
    backoff_max: float = 32.0
    backoff_attempts: int = 5


@dataclass
class ExchangePair:
    symbol: str
    timeframes: List[str]


@dataclass
class Config:
    settings: Settings
    exchanges: Dict[str, List[ExchangePair]]


@dataclass
class OHLCVRecord:
    timestamp: datetime
    exchange: str
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    ingested_at: datetime

    def to_bq_row(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "exchange": self.exchange,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "ingested_at": self.ingested_at.isoformat(),
        }

