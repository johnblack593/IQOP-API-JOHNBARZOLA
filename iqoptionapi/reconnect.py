"""
iqoptionapi/reconnect.py
Exponential backoff reconnection manager with jitter and attempt ceiling.
"""
import time
import random
import threading
from iqoptionapi.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_BASE   = 2       # seconds — base of the exponential
_DEFAULT_CAP    = 60      # seconds — maximum wait ceiling
_DEFAULT_MAX    = 10      # maximum reconnection attempts before raising
_JITTER_RANGE   = 0.5     # ±50% jitter on calculated wait


class MaxReconnectAttemptsError(Exception):
    """Raised when reconnection attempts are exhausted."""
    pass


class ReconnectManager:
    """
    Thread-safe exponential backoff manager.

    Usage:
        rm = ReconnectManager()
        while not connected:
            rm.wait()          # blocks; raises MaxReconnectAttemptsError at ceiling
            connected = try_connect()
        rm.reset()             # call on successful connection
    """

    def __init__(self, base=_DEFAULT_BASE, cap=_DEFAULT_CAP,
                 max_attempts=_DEFAULT_MAX):
        self._base        = base
        self._cap         = cap
        self._max         = max_attempts
        self._attempt     = 0
        self._lock        = threading.Lock()

    def wait(self):
        """Block for the computed backoff duration. Raises on max attempts."""
        with self._lock:
            self._attempt += 1
            if self._attempt > self._max:
                logger.error(
                    "ReconnectManager: max attempts (%d) exhausted. "
                    "Raising MaxReconnectAttemptsError.", self._max
                )
                raise MaxReconnectAttemptsError(
                    f"Reconnection failed after {self._max} attempts."
                )
            raw_wait  = min(self._base ** self._attempt, self._cap)
            jitter    = raw_wait * _JITTER_RANGE * (2 * random.random() - 1)
            wait_time = max(0.0, raw_wait + jitter)

        logger.warning(
            "ReconnectManager: attempt %d/%d — waiting %.2fs before reconnect.",
            self._attempt, self._max, wait_time
        )
        time.sleep(wait_time)

    def reset(self):
        """Reset attempt counter after a successful connection."""
        with self._lock:
            self._attempt = 0
        logger.info("ReconnectManager: connection restored — counter reset.")

    @property
    def attempts(self) -> int:
        with self._lock:
            return self._attempt
