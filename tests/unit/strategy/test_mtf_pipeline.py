"""Unit tests for MTFPipeline and MTFSnapshot."""
import math
import numpy as np
import pytest
from collections import deque
from unittest.mock import MagicMock

from iqoptionapi.strategy.mtf_pipeline import MTFPipeline, MIN_CANDLES
from iqoptionapi.strategy.mtf_snapshot import MTFSnapshot, TimeframeIndicators


def _make_cache(active_id: int, size: int, n: int, seed: int = 42):
    """Crea un CandleCache mock con n velas sintéticas OHLC."""
    rng = np.random.default_rng(seed)
    closes = 1.1000 + np.cumsum(rng.normal(0, 0.0005, n))
    candles = [
        {
            "open":  float(closes[i] - rng.uniform(0, 0.0003)),
            "close": float(closes[i]),
            "max":   float(closes[i] + rng.uniform(0, 0.0003)),
            "min":   float(closes[i] - rng.uniform(0, 0.0003)),
            "volume": float(rng.integers(100, 1000)),
        }
        for i in range(n)
    ]
    # invertir para simular "más recientes primero" como hace CandleCache
    candles_reversed = list(reversed(candles))

    mock_cache = MagicMock()
    mock_cache.get_candles.return_value = candles_reversed
    return mock_cache


class TestTimeframeIndicators:
    def test_has_data_true_when_rsi_valid(self):
        tf = TimeframeIndicators(timeframe=60, candles_used=50, rsi_14=55.0)
        assert tf.has_data is True

    def test_has_data_false_when_rsi_nan(self):
        tf = TimeframeIndicators(timeframe=60, candles_used=5)
        assert tf.has_data is False

    def test_bias_call_when_rsi_oversold_and_macd_positive(self):
        tf = TimeframeIndicators(
            timeframe=60, candles_used=50,
            rsi_14=35.0, macd_hist=0.001
        )
        assert tf.bias == 'CALL'

    def test_bias_put_when_rsi_overbought_and_macd_negative(self):
        tf = TimeframeIndicators(
            timeframe=60, candles_used=50,
            rsi_14=65.0, macd_hist=-0.001
        )
        assert tf.bias == 'PUT'

    def test_bias_neutral_when_conflicting_signals(self):
        tf = TimeframeIndicators(
            timeframe=60, candles_used=50,
            rsi_14=35.0, macd_hist=-0.001  # RSI dice CALL, MACD dice PUT
        )
        assert tf.bias == 'NEUTRAL'


class TestMTFSnapshot:
    def test_available_timeframes_empty_when_no_data(self):
        snap = MTFSnapshot(asset="EURUSD")
        assert snap.available_timeframes == []

    def test_multi_tf_bias_majority_wins(self):
        tf_call = TimeframeIndicators(timeframe=60,  candles_used=50, rsi_14=35.0, macd_hist=0.001)
        tf_put  = TimeframeIndicators(timeframe=300, candles_used=50, rsi_14=65.0, macd_hist=-0.001)
        tf_call2= TimeframeIndicators(timeframe=900, candles_used=50, rsi_14=35.0, macd_hist=0.001)
        snap = MTFSnapshot(asset="EURUSD", m1=tf_call, m5=tf_put, m15=tf_call2)
        assert snap.multi_tf_bias == 'CALL'


class TestMTFPipeline:
    def test_compute_returns_snapshot_with_asset_name(self):
        cache = _make_cache(1, 60, MIN_CANDLES + 10)
        pipeline = MTFPipeline(cache)
        snap = pipeline.compute(active_id=1, asset="EURUSD")
        assert isinstance(snap, MTFSnapshot)
        assert snap.asset == "EURUSD"

    def test_compute_insufficient_candles_returns_nan_tf(self):
        mock_cache = MagicMock()
        mock_cache.get_candles.return_value = []  # sin velas
        pipeline = MTFPipeline(mock_cache)
        snap = pipeline.compute(active_id=1, asset="EURUSD")
        assert snap.m1 is not None
        assert snap.m1.has_data is False
        assert math.isnan(snap.m1.rsi_14)

    def test_compute_sufficient_candles_returns_valid_rsi(self):
        cache = _make_cache(1, 60, MIN_CANDLES + 20)
        pipeline = MTFPipeline(cache)
        snap = pipeline.compute(active_id=1, asset="EURUSD")
        # Con suficientes velas, RSI debe ser un número en 
        assert not math.isnan(snap.m1.rsi_14)
        assert 0.0 <= snap.m1.rsi_14 <= 100.0

    def test_compute_all_indicators_not_nan_with_enough_data(self):
        cache = _make_cache(1, 60, MIN_CANDLES + 20)
        pipeline = MTFPipeline(cache)
        snap = pipeline.compute(active_id=1, asset="EURUSD")
        tf = snap.m1
        assert not math.isnan(tf.sma_20)
        assert not math.isnan(tf.ema_20)
        assert not math.isnan(tf.macd_line)
        assert not math.isnan(tf.atr_14)
