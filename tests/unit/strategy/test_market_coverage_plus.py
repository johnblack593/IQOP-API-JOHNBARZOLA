"""
tests/unit/strategy/test_market_coverage_plus.py
────────────────────────────────────────────────
Tests adicionales para maximizar cobertura en módulos de inteligencia.
"""
import pytest
from unittest.mock import MagicMock
from iqoptionapi.strategy.market_quality import MarketQualityMonitor
from iqoptionapi.strategy.market_regime import MarketRegime

def make_cache_with_ask_bid():
    cache = MagicMock()
    # 5 velas con ask/bid, 5 con max/min/open proxy
    candles = [
        {"ask": 1.1005, "bid": 1.1000, "volume": 500} for _ in range(5)
    ] + [
        {"max": 1.1010, "min": 1.1000, "open": 1.1005, "volume": 100} for _ in range(5)
    ]
    cache.get_candles.return_value = candles
    return cache

class TestMarketQualityDeep:
    def test_get_spread_with_mixed_data(self):
        mq = MarketQualityMonitor(make_cache_with_ask_bid())
        spread = mq.get_spread(1, 60, n=10)
        # ask-bid = 0.0005 (5 velas)
        # (max-min)/open = (0.0010)/1.1005 = 0.000908... (5 velas)
        # Promedio: (0.0025 + 0.00454) / 10 = 0.000704...
        assert 0.0006 < spread < 0.0008

    def test_get_quality_score_low_volume_consistency(self):
        cache = MagicMock()
        # Volumen muy inconsistente para bajar el score
        candles = [
            {"ask": 1.1001, "bid": 1.1000, "volume": 10},
            {"ask": 1.1001, "bid": 1.1000, "volume": 1000},
            {"ask": 1.1001, "bid": 1.1000, "volume": 50},
            {"ask": 1.1001, "bid": 1.1000, "volume": 5000},
            {"ask": 1.1001, "bid": 1.1000, "volume": 5},
        ]
        cache.get_candles.return_value = candles
        mq = MarketQualityMonitor(cache)
        score = mq.get_quality_score(1, 60)
        # Spread score debe ser alto (spread bajo)
        # Vol score debe ser bajo (CV alto)
        assert score < 0.9  # No debe ser perfecto

    def test_get_summary_format(self):
        mq = MarketQualityMonitor(make_cache_with_ask_bid())
        summary = mq.get_summary(1, 60)
        assert "spread" in summary
        assert "quality_score" in summary
        assert "is_tradeable" in summary
        assert summary["n_candles_analyzed"] == 10

class TestMarketRegimeDeep:
    def test_get_trend_direction_up(self):
        cache = MagicMock()
        # Mocking ADX > 25 (trending) and +DI > -DI
        candles = []
        base = 1.1000
        # Velas ascendentes
        for i in range(40):
            base += 0.0010
            candles.append({"max": base + 0.0005, "min": base - 0.0005, "close": base, "open": base - 0.0002})
        # Reversed because the code does reversed(candles)
        cache.get_candles.return_value = list(reversed(candles))
        mr = MarketRegime(cache)
        
        mr.get_regime = MagicMock(return_value="trending")
        direction = mr.get_trend_direction(1, 60)
        # Note: get_trend_direction also reverses candles internally if they are not reversed
        # Actually it does candles = list(reversed(candles))
        # So if I pass them already reversed, they will be reversed again to normal order.
        # Let's just pass them in normal order.
        cache.get_candles.return_value = candles
        direction = mr.get_trend_direction(1, 60)
        assert direction == "up"

    def test_get_trend_direction_down(self):
        cache = MagicMock()
        candles = []
        base = 1.1000
        for i in range(40):
            base -= 0.0010
            candles.append({"max": base + 0.0005, "min": base - 0.0005, "close": base, "open": base + 0.0002})
        cache.get_candles.return_value = candles
        mr = MarketRegime(cache)
        mr.get_regime = MagicMock(return_value="trending")
        direction = mr.get_trend_direction(1, 60)
        assert direction == "down"

    def test_get_summary_extended(self):
        cache = MagicMock()
        cache.get_candles.return_value = [{"max": 1, "min": 0.5, "close": 0.8}] * 40
        mr = MarketRegime(cache)
        summary = mr.get_summary(1, 60)
        assert "adx" in summary
        assert "regime" in summary
        assert summary["is_reliable"] == True
