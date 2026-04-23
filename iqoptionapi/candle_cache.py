"""
iqoptionapi/candle_cache.py
───────────────────────────
Cache de velas con límite de buffer (deque) y expiración por TTL.
Evita el crecimiento indefinido de memoria (RSS).
"""
from collections import deque
import time
from iqoptionapi import config

class CandleCache:
    """
    Cache de velas que utiliza deque(maxlen) para estabilizar el consumo de RAM.
    """

    def __init__(self) -> None:
        # { (active_id, size): deque([candles], maxlen=CANDLE_BUFFER_MAX) }
        self._cache: dict[tuple, deque] = {}
        self._maxlen: int = config.CANDLE_BUFFER_MAX

    def _get_or_create_buffer(self, active_id: int, size: int) -> deque:
        key = (active_id, size)
        if key not in self._cache:
            self._cache[key] = deque(maxlen=self._maxlen)
        return self._cache[key]

    def add_candle(self, active_id: int, size: int, candle: dict) -> None:
        """Agrega una vela al buffer con timestamp de inserción para TTL."""
        candle["_ts"] = time.time()
        self._get_or_create_buffer(active_id, size).appendleft(candle)

    def get_candles(self, active_id: int, size: int, n: int | None = None) -> list[dict]:
        """Retorna las velas del buffer (opcionalmente limitado a n)."""
        buf = self._get_or_create_buffer(active_id, size)
        candles = list(buf)
        if n:
            candles = candles[:n]
        return candles

    def set_maxlen(self, active_id: int, size: int, maxlen: int) -> None:
        """Ajusta dinámicamente el tamaño del buffer para un activo+timeframe."""
        key = (active_id, size)
        if key in self._cache:
            # Recrear deque con nuevo maxlen si cambió
            if self._cache[key].maxlen != maxlen:
                self._cache[key] = deque(self._cache[key], maxlen=maxlen)
        else:
            self._cache[key] = deque(maxlen=maxlen)

    def evict_expired(self) -> int:
        """
        Elimina velas más antiguas que config.CANDLE_TTL_SECONDS.
        Retorna la cantidad total de velas eliminadas.
        """
        cutoff = time.time() - config.CANDLE_TTL_SECONDS
        removed = 0
        for key, buf in list(self._cache.items()):
            original_len = len(buf)
            # deque no soporta filter in-place — reconstruimos
            fresh = deque(
                (c for c in buf if c.get("_ts", 0) > cutoff),
                maxlen=buf.maxlen
            )
            self._cache[key] = fresh
            removed += original_len - len(fresh)
        return removed

    def stats(self) -> dict:
        return {
            "buffers": len(self._cache),
            "total_candles": sum(len(d) for d in self._cache.values())
        }
