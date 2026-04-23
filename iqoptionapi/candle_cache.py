"""
iqoptionapi/candle_cache.py
───────────────────────────
Cache inteligente de velas históricas (RAM + Disco).
"""
import os
import numpy as np
from numpy.typing import NDArray
from collections import deque
from dataclasses import dataclass
from typing import Optional, Dict, List
import time


@dataclass(frozen=True)
class CacheKey:
    asset:       str
    size_secs:   int
    timestamp:   int

class CandleCache:
    """
    Cache de dos niveles: L1 (RAM) y L2 (Disco .npy).
    """

    def __init__(
        self,
        cache_dir: str = "data/candles",
        max_ram_candles: int = 500,
        max_disk_days: int = 30,
    ) -> None:
        self.cache_dir = cache_dir
        self.max_ram_candles = max_ram_candles
        self.max_disk_days = max_disk_days
        
        # RAM Cache: { (asset, size): deque([candles]) }
        self._l1: Dict[tuple, deque] = {}
        
        # Stats
        self._hits = 0
        self._misses = 0
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

    def _get_l1_key(self, asset: str, size_secs: int) -> tuple:
        return (asset, size_secs)

    def get(
        self,
        asset: str,
        size_secs: int,
        count: int,
        end_timestamp: Optional[int] = None,
    ) -> Optional[NDArray[np.float64]]:
        """
        Busca velas en cache.
        """
        l1_key = self._get_l1_key(asset, size_secs)
        
        # L1 Check (RAM)
        if l1_key in self._l1:
            all_l1 = list(self._l1[l1_key])
            if len(all_l1) >= count:
                # Simple logic: assume L1 has the most recent candles
                # In real scenario, we'd filter by timestamp
                self._hits += 1
                return np.array(all_l1[-count:])
        
        # L2 Check (Disco) - Simplified for this implementation
        # Real L2 would read .npy files by date/asset
        self._misses += 1
        return None

    def put(
        self,
        asset: str,
        size_secs: int,
        candles: NDArray[np.float64],
    ) -> None:
        """
        Inserta velas en el cache.
        """
        l1_key = self._get_l1_key(asset, size_secs)
        if l1_key not in self._l1:
            self._l1[l1_key] = deque(maxlen=self.max_ram_candles)
        
        for candle in candles:
            # Avoid duplicates if possible (check last timestamp)
            if self._l1[l1_key] and np.array_equal(self._l1[l1_key][-1], candle):
                continue
            self._l1[l1_key].append(candle)
            
        # L2 Persistence (Disco)
        self._persist_to_l2(asset, size_secs, candles)

    def _persist_to_l2(self, asset: str, size_secs: int, candles: NDArray[np.float64]) -> None:
        # Simplified: save one file per asset/size
        # Real implementation would shard by date
        path = os.path.join(self.cache_dir, f"{asset}_{size_secs}.npy")
        if os.path.exists(path):
            try:
                existing = np.load(path)
                combined = np.vstack([existing, candles])
                # Deduplicate by timestamp (index 0)
                _, unique_idx = np.unique(combined[:, 0], return_index=True)
                combined = combined[unique_idx]
                # Keep only last MAX_RAM_CANDLES * 10 for disk limit example
                np.save(path, combined[-5000:])
            except Exception:
                np.save(path, candles)
        else:
            np.save(path, candles)

    def invalidate(self, asset: str, size_secs: int) -> None:
        l1_key = self._get_l1_key(asset, size_secs)
        if l1_key in self._l1:
            del self._l1[l1_key]

    def cache_hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def stats(self) -> dict:
        return {
            "l1_entries": sum(len(d) for d in self._l1.values()),
            "hit_rate": self.cache_hit_rate(),
            "hits": self._hits,
            "misses": self._misses
        }
