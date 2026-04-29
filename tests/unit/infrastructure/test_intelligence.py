"""
Tests para los módulos de inteligencia de mercado.
Verifican graceful degradation con candle_cache vacío.
"""
import pytest
from unittest.mock import MagicMock

def make_empty_cache():
    cache = MagicMock()
    cache.get_candles.return_value = []
    return cache

def make_cache_with_candles(n=20):
    import random
    base = 1.1000
    candles = []
    for i in range(n):
        o = base + random.uniform(-0.001, 0.001)
        c = o + random.uniform(-0.0005, 0.0005)
        h = max(o, c) + random.uniform(0, 0.0003)
        l = min(o, c) - random.uniform(0, 0.0003)
        candles.append({"open": o, "close": c, "max": h, "min": l, "volume": 100})
    cache = MagicMock()
    cache.get_candles.return_value = candles
    return cache

class TestMarketQuality:
    def test_empty_cache_returns_safe_defaults(self):
        from iqoptionapi.strategy.market_quality import MarketQualityMonitor
        mq = MarketQualityMonitor(make_empty_cache())
        assert mq.get_spread(1, 60) == 0.0
        assert mq.is_tradeable(1, 60) == True  # fail-open
        assert 0.0 <= mq.get_quality_score(1, 60) <= 1.0

class TestPatternEngine:
    def test_empty_cache_returns_empty_list(self):
        from iqoptionapi.strategy.pattern_engine import PatternEngine
        pe = PatternEngine(make_empty_cache())
        assert pe.detect(1, 60) == []

    def test_detects_patterns_with_data(self):
        from iqoptionapi.strategy.pattern_engine import PatternEngine
        pe = PatternEngine(make_cache_with_candles(20))
        result = pe.detect(1, 60)
        assert isinstance(result, list)

class TestMarketRegime:
    def test_insufficient_data_returns_transitioning(self):
        from iqoptionapi.strategy.market_regime import MarketRegime
        mr = MarketRegime(make_empty_cache())
        assert mr.get_regime(1, 60) == "transitioning"
        assert mr.get_adx(1, 60) == -1.0

    def test_with_data_returns_valid_regime(self):
        from iqoptionapi.strategy.market_regime import MarketRegime
        mr = MarketRegime(make_cache_with_candles(40))
        regime = mr.get_regime(1, 60)
        assert regime in ("trending", "ranging", "transitioning")

class TestCorrelationEngine:
    def test_empty_cache_returns_zero(self):
        from iqoptionapi.strategy.correlation_engine import CorrelationEngine
        ce = CorrelationEngine(make_empty_cache())
        assert ce.get_correlation(1, 2, 60) == 0.0

    def test_identical_assets_have_correlation_one(self):
        """Dos activos con los mismos cierres deben tener correlación 1.0."""
        from iqoptionapi.strategy.correlation_engine import CorrelationEngine
        import random
        prices = [1.1 + i * 0.001 for i in range(30)]
        candles = [{"close": p, "open": p, "max": p, "min": p} for p in prices]
        cache = MagicMock()
        cache.get_candles.return_value = candles
        ce = CorrelationEngine(cache)
        result = ce.get_correlation(1, 1, 60, n=30)
        assert abs(result - 1.0) < 0.001

