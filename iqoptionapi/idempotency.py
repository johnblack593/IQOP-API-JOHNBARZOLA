"""
iqoptionapi/idempotency.py
Order idempotency key registry — prevents duplicate order submission
on timeout/retry scenarios.
"""
import uuid
import threading
import time
from iqoptionapi.logger import get_logger

logger = get_logger(__name__)

_TTL_SECONDS = 300   # 5-minute window; orders older than this are auto-expired


class IdempotencyRegistry:
    """
    In-memory registry that tracks in-flight and recently-completed orders
    by a client-generated request_id (UUID4).

    States:
        PENDING   — order submitted to WS, awaiting server confirmation
        CONFIRMED — server returned an order_id for this request
        FAILED    — timeout or explicit failure; safe to discard or retry
    """

    PENDING   = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED    = "FAILED"

    def __init__(self):
        self._store: dict[str, dict] = {}
        self._lock  = threading.Lock()

    # ------------------------------------------------------------------

    def register(self) -> str:
        """
        Create and store a new pending request_id.
        Returns the UUID string to attach to the outgoing order.
        """
        request_id = str(uuid.uuid4())
        with self._lock:
            self._store[request_id] = {
                "state":      self.PENDING,
                "created_at": time.monotonic(),
                "order_id":   None,
            }
        logger.debug("Idempotency: registered request_id=%s", request_id)
        return request_id

    def confirm(self, request_id: str, order_id) -> None:
        """Mark a pending request as confirmed with the server's order_id."""
        with self._lock:
            if request_id in self._store:
                self._store[request_id]["state"]    = self.CONFIRMED
                self._store[request_id]["order_id"] = order_id
                logger.info(
                    "Idempotency: CONFIRMED request_id=%s → order_id=%s",
                    request_id, order_id
                )

    def fail(self, request_id: str) -> None:
        """Mark a pending request as failed (timeout or explicit error)."""
        with self._lock:
            if request_id in self._store:
                self._store[request_id]["state"] = self.FAILED
                logger.warning(
                    "Idempotency: FAILED request_id=%s — order status unknown. "
                    "Do NOT retry automatically.", request_id
                )

    def is_pending(self, request_id: str) -> bool:
        with self._lock:
            entry = self._store.get(request_id)
            return entry is not None and entry["state"] == self.PENDING

    def get_order_id(self, request_id: str):
        """Returns confirmed server order_id, or None if not yet confirmed."""
        with self._lock:
            entry = self._store.get(request_id)
            if entry and entry["state"] == self.CONFIRMED:
                return entry["order_id"]
            return None

    def purge_expired(self) -> int:
        """Remove entries older than _TTL_SECONDS. Returns count purged."""
        now = time.monotonic()
        purged = 0
        with self._lock:
            expired = [
                k for k, v in self._store.items()
                if now - v["created_at"] > _TTL_SECONDS
            ]
            for k in expired:
                del self._store[k]
                purged += 1
        if purged:
            logger.debug("Idempotency: purged %d expired entries.", purged)
        return purged
