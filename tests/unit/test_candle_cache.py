"""
Tests para CandleCache (versión simple con deque y TTL).
"""
import pytest
import time
from iqoptionapi.candle_cache import CandleCache

class TestCandleCache:
    @pytest.fixture
    def cache(self):
        return CandleCache()

    def test_add_and_get_candles(self, cache):
        candle = {"at": 100, "open": 1.1, "close": 1.2}
        cache.add_candle(1, 60, candle)
        
        candles = cache.get_candles(1, 60)
        assert len(candles) == 1
        assert candles[0]["at"] == 100

    def test_maxlen_enforced(self, cache):
        # El maxlen por defecto viene de config.CANDLE_BUFFER_MAX
        # Pero podemos ajustarlo con set_maxlen
        cache.set_maxlen(1, 60, 2)
        
        cache.add_candle(1, 60, {"at": 100})
        cache.add_candle(1, 60, {"at": 110})
        cache.add_candle(1, 60, {"at": 120})
        
        candles = cache.get_candles(1, 60)
        assert len(candles) == 2
        # deque(appendleft) -> [120, 110]
        assert candles[0]["at"] == 120
        assert candles[1]["at"] == 110

    def test_stats(self, cache):
        cache.add_candle(1, 60, {"at": 100})
        stats = cache.stats()
        assert stats["buffers"] == 1
        assert stats["total_candles"] == 1
