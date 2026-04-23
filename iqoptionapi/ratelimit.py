"""
iqoptionapi/ratelimit.py
Token bucket rate limiter for order submission.
Prevents runaway bots from flooding the API with orders.
"""
import threading
import time
import functools
from iqoptionapi.logger import get_logger
from iqoptionapi.config import (
    RATE_LIMIT_CAPACITY, RATE_LIMIT_REFILL
)

logger = get_logger(__name__)


class RateLimitExceededError(Exception):
    """Raised when an order is rejected due to rate limit enforcement."""
    pass


class TokenBucket:
    """
    Token bucket algorithm.
    Default: 5 orders per 10 seconds (refill_rate=0.5 tokens/sec, capacity=5).
    These defaults are conservative — IQ Option's observed practical limit
    is higher, but we enforce a safe floor on the client side.

    Parameters:
        capacity      — maximum burst size (tokens)
        refill_rate   — tokens added per second
        block         — if True, wait for a token instead of raising
    """

    def __init__(self, capacity: float = RATE_LIMIT_CAPACITY,
                 refill_rate: float = RATE_LIMIT_REFILL,
                 block: bool = False):
        self._capacity    = capacity
        self._tokens      = capacity
        self._refill_rate = refill_rate
        self._block       = block
        self._last_refill = time.monotonic()
        self._lock        = threading.Lock()

    def _refill(self) -> None:
        now     = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self._capacity,
            self._tokens + elapsed * self._refill_rate
        )
        self._last_refill = now

    def consume(self) -> None:
        """
        Consume one token. Raises RateLimitExceededError if no tokens
        available and block=False. Blocks until a token is available
        if block=True.
        """
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait_time = (1.0 - self._tokens) / self._refill_rate

            if self._block:
                logger.warning(
                    "RateLimiter: token bucket empty — waiting %.2fs", wait_time
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    "RateLimiter: order REJECTED — rate limit exceeded. "
                    "Retry in %.2fs.", wait_time
                )
                raise RateLimitExceededError(
                    f"Order rate limit exceeded. Retry in {wait_time:.2f}s."
                )

    @property
    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens


def rate_limited(bucket_attr: str):
    """
    Decorator to apply rate limiting using a bucket stored in an instance attribute.
    :param bucket_attr: Name of the attribute containing the TokenBucket instance.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            bucket = getattr(self, bucket_attr, None)
            if bucket and isinstance(bucket, TokenBucket):
                bucket.consume()
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


