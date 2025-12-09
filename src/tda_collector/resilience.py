import random
import time
from typing import Callable, Tuple, Optional

import ccxt

RETRY_EXCEPTIONS = (ccxt.NetworkError, ccxt.RateLimitExceeded)


def retry_with_backoff(
    func: Callable,
    func_args: Tuple,
    *,
    base_delay: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 32.0,
    max_attempts: int = 5,
    sleep_fn: Optional[Callable[[float], None]] = None,
    jitter_fn: Optional[Callable[[float], float]] = None,
):
    """
    Execute func with retries on ccxt network/rate limit errors.
    """
    attempt = 0
    sleep_fn = sleep_fn or time.sleep
    jitter_fn = jitter_fn or (lambda bd: random.uniform(0, bd))

    while True:
        attempt += 1
        try:
            return func(*func_args)
        except RETRY_EXCEPTIONS as exc:
            if attempt >= max_attempts:
                raise
            sleep_for = min(max_delay, base_delay * (factor ** (attempt - 1)))
            sleep_for += jitter_fn(base_delay)
            sleep_fn(sleep_for)
        except Exception:
            # Non-retryable
            raise

