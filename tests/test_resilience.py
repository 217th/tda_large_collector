import ccxt

from tda_collector.resilience import retry_with_backoff


def test_retry_with_backoff_retries_and_raises_after_max():
    attempts = {"count": 0}

    def will_fail(*args, **kwargs):
        attempts["count"] += 1
        raise ccxt.NetworkError("nope")

    sleeps = []

    def fake_sleep(delay):
        sleeps.append(delay)

    def fake_jitter(base):
        return 0

    try:
        retry_with_backoff(
            will_fail,
            (),
            max_attempts=3,
            base_delay=0.01,
            factor=2.0,
            max_delay=0.1,
            sleep_fn=fake_sleep,
            jitter_fn=fake_jitter,
        )
    except ccxt.NetworkError:
        pass

    assert attempts["count"] == 3
    # delays: 0.01, 0.02 (min with max_delay), 0.04 -> but we stop after 3rd raise before sleeping again
    assert len(sleeps) == 2
    assert sleeps[0] == 0.01

