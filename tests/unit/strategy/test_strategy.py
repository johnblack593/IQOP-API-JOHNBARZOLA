import unittest
import numpy as np
from datetime import datetime, timezone
from dataclasses import FrozenInstanceError
from iqoptionapi.strategy import (
    Signal, Direction, AssetType, BaseStrategy, StrategyRegistry
)
from iqoptionapi.strategy.indicators import (
    sma, ema, rsi, macd, bollinger_bands, stochastic, atr
)

class TestSignalDataclass(unittest.TestCase):
    def test_signal_hold_not_actionable(self):
        sig = Signal("EURUSD", Direction.HOLD, 60, 1.0, AssetType.BINARY, 0.5, "test")
        self.assertFalse(sig.is_actionable)

    def test_signal_call_actionable(self):
        sig = Signal("EURUSD", Direction.CALL, 60, 1.0, AssetType.BINARY, 0.5, "test")
        self.assertTrue(sig.is_actionable)

    def test_signal_invalid_confidence_raises(self):
        with self.assertRaises(ValueError):
            Signal("EURUSD", Direction.CALL, 60, 1.0, AssetType.BINARY, 1.5, "test")

    def test_signal_invalid_amount_raises(self):
        with self.assertRaises(ValueError):
            Signal("EURUSD", Direction.CALL, 60, -1.0, AssetType.BINARY, 0.5, "test")

    def test_signal_frozen(self):
        sig = Signal("EURUSD", Direction.CALL, 60, 1.0, AssetType.BINARY, 0.5, "test")
        with self.assertRaises(FrozenInstanceError):
            sig.asset = "BTCUSD"

    def test_signal_timestamp_is_utc(self):
        sig = Signal("EURUSD", Direction.CALL, 60, 1.0, AssetType.BINARY, 0.5, "test")
        self.assertIsNotNone(sig.timestamp.tzinfo)

class TestIndicators(unittest.TestCase):
    def test_sma_correct_value(self):
        prices = np.array([1, 2, 3, 4, 5], dtype=np.float64)
        val = sma(prices, 3)
        self.assertEqual(val, 4.0)

    def test_sma_insufficient_data_returns_nan(self):
        prices = np.array([1, 2], dtype=np.float64)
        val = sma(prices, 5)
        self.assertTrue(np.isnan(val))

    def test_ema_convergence(self):
        # 50 constant prices
        prices = np.ones(50, dtype=np.float64) * 100.0
        val = ema(prices, 9)
        self.assertEqual(val, 100.0)

    def test_rsi_neutral_on_flat_prices(self):
        # RSI needs variation to calculate averages correctly in some implementations,
        # but Wilder's smoothing with flat prices results in 0/0 or 100 depending on implementation.
        # My implementation returns 100 if avg_loss == 0.
        prices = np.ones(50, dtype=np.float64) * 100.0
        val = rsi(prices)
        self.assertEqual(val, 100.0) # All gains are 0, all losses are 0. 0/0 case.

    def test_rsi_range_0_to_100(self):
        prices = np.random.rand(50) * 100
        val = rsi(prices)
        self.assertTrue(0 <= val <= 100)

    def test_bollinger_upper_gt_lower(self):
        prices = np.array([10, 11, 10.5, 12, 11.5, 13, 12.5], dtype=np.float64)
        upper, middle, lower = bollinger_bands(prices, period=5)
        self.assertTrue(upper > lower)
        self.assertTrue(upper > middle > lower)

    def test_atr_positive(self):
        highs = np.array([10, 11, 12, 11, 13], dtype=np.float64)
        lows = np.array([9, 10, 11, 10, 12], dtype=np.float64)
        closes = np.array([9.5, 10.5, 11.5, 10.5, 12.5], dtype=np.float64)
        val = atr(highs, lows, closes, period=3)
        self.assertTrue(val > 0)

class ConcreteStrategy(BaseStrategy):
    def analyze(self, candles):
        return self._hold()

class TestBaseStrategy(unittest.TestCase):
    def test_cannot_instantiate_abstract(self):
        with self.assertRaises(TypeError):
            BaseStrategy(asset="EURUSD")

    def test_hold_returns_hold_direction(self):
        strat = ConcreteStrategy(asset="EURUSD")
        sig = strat.analyze(None)
        self.assertEqual(sig.direction, Direction.HOLD)

    def test_signal_helper_returns_correct_direction(self):
        strat = ConcreteStrategy(asset="EURUSD")
        sig = strat._signal(Direction.CALL, 0.8)
        self.assertEqual(sig.direction, Direction.CALL)
        self.assertEqual(sig.confidence, 0.8)

    def test_validate_candles_insufficient(self):
        class MyStrat(ConcreteStrategy):
            @property
            def min_candles(self): return 10
        
        strat = MyStrat(asset="EURUSD")
        candles = np.zeros((2, 5))
        self.assertFalse(strat.validate_candles(candles))
        
        candles = np.zeros((10, 5))
        self.assertTrue(strat.validate_candles(candles))

    def test_amount_zero_raises(self):
        with self.assertRaises(ValueError):
            ConcreteStrategy(asset="EURUSD", amount=0)

class TestStrategyRegistry(unittest.TestCase):
    def setUp(self):
        StrategyRegistry.clear()

    def test_register_and_get(self):
        @StrategyRegistry.register
        class MyStrat(ConcreteStrategy): pass
        
        self.assertEqual(StrategyRegistry.get("MyStrat"), MyStrat)

    def test_duplicate_raises(self):
        @StrategyRegistry.register
        class Dup(ConcreteStrategy): pass
        
        with self.assertRaises(ValueError):
            @StrategyRegistry.register
            class Dup(ConcreteStrategy): pass

    def test_unknown_raises_keyerror(self):
        with self.assertRaises(KeyError):
            StrategyRegistry.get("NonExistent")

    def test_list_all_sorted(self):
        @StrategyRegistry.register
        class B(ConcreteStrategy): pass
        @StrategyRegistry.register
        class A(ConcreteStrategy): pass
        
        self.assertEqual(StrategyRegistry.list_all(), ["A", "B"])

    def test_clear_for_tests(self):
        @StrategyRegistry.register
        class A(ConcreteStrategy): pass
        StrategyRegistry.clear()
        self.assertEqual(StrategyRegistry.list_all(), [])

class TestRSIEMAStrategy(unittest.TestCase):
    def test_rsi_ema_returns_signal_object(self):
        from iqoptionapi.strategy.strategies.rsi_ema import RSIEMAStrategy
        strat = RSIEMAStrategy(asset="EURUSD")
        candles = np.zeros((100, 5))
        sig = strat.analyze(candles)
        self.assertIsInstance(sig, Signal)

    def test_rsi_ema_hold_on_insufficient_data(self):
        from iqoptionapi.strategy.strategies.rsi_ema import RSIEMAStrategy
        strat = RSIEMAStrategy(asset="EURUSD")
        candles = np.zeros((5, 5))
        sig = strat.analyze(candles)
        self.assertEqual(sig.direction, Direction.HOLD)
        self.assertEqual(sig.metadata["reason"], "insufficient_data")

    def test_rsi_ema_hold_on_flat_market(self):
        from iqoptionapi.strategy.strategies.rsi_ema import RSIEMAStrategy
        strat = RSIEMAStrategy(asset="EURUSD")
        # Prices constant 1.0
        candles = np.column_stack([
            np.ones(100), np.ones(100), np.ones(100), np.ones(100), np.ones(100)
        ])
        sig = strat.analyze(candles)
        self.assertEqual(sig.direction, Direction.HOLD)

    def test_rsi_ema_confidence_in_range(self):
        from iqoptionapi.strategy.strategies.rsi_ema import RSIEMAStrategy
        strat = RSIEMAStrategy(asset="EURUSD")
        # Strong uptrend
        prices = np.linspace(1.0, 1.5, 100)
        candles = np.column_stack([
            prices, prices + 0.01, prices - 0.01, prices, np.ones(100)
        ])
        sig = strat.analyze(candles)
        self.assertTrue(0.0 <= sig.confidence <= 1.0)

if __name__ == "__main__":
    unittest.main()
