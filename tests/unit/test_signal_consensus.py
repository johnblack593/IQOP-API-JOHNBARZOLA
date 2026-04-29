import unittest
import numpy as np
from iqoptionapi.strategy.signal_consensus import SignalConsensus, ConsensusResult
from iqoptionapi.strategy.base import BaseStrategy
from iqoptionapi.strategy.signal import Signal, Direction, AssetType

class MockStrategy(BaseStrategy):
    def __init__(self, name, direction, confidence):
        super().__init__("EURUSD")
        self._name = name
        self._direction = direction
        self._confidence = confidence
    
    @property
    def name(self): return self._name

    def analyze(self, candles):
        return self._signal(self._direction, self._confidence)

class TestSignalConsensus(unittest.TestCase):
    def test_requires_minimum_2_strategies(self):
        with self.assertRaises(ValueError):
            SignalConsensus(strategies=[MockStrategy("S1", Direction.CALL, 0.8)])

    def test_unanimous_call_is_actionable(self):
        s1 = MockStrategy("S1", Direction.CALL, 0.8)
        s2 = MockStrategy("S2", Direction.CALL, 0.9)
        consensus = SignalConsensus(strategies=[s1, s2], min_agreement=1.0)
        res = consensus.evaluate(np.zeros((10, 5)))
        self.assertEqual(res.direction, Direction.CALL)
        self.assertTrue(res.is_actionable)
        self.assertEqual(res.agreement_ratio, 1.0)

    def test_split_50_50_returns_hold(self):
        s1 = MockStrategy("S1", Direction.CALL, 0.8)
        s2 = MockStrategy("S2", Direction.PUT, 0.8)
        consensus = SignalConsensus(strategies=[s1, s2])
        res = consensus.evaluate(np.zeros((10, 5)))
        self.assertEqual(res.direction, Direction.HOLD)
        self.assertFalse(res.is_actionable)

    def test_below_min_agreement_returns_hold_in_actionable(self):
        s1 = MockStrategy("S1", Direction.CALL, 0.8)
        s2 = MockStrategy("S2", Direction.CALL, 0.8)
        s3 = MockStrategy("S3", Direction.PUT, 0.8)
        # Agreement is 2/3 = 0.666
        consensus = SignalConsensus(strategies=[s1, s2, s3], min_agreement=0.75)
        res = consensus.evaluate(np.zeros((10, 5)))
        self.assertEqual(res.direction, Direction.CALL) # Majority is CALL
        self.assertFalse(res.is_actionable) # But ratio 0.67 < 0.75

    def test_failed_strategy_excluded_not_crash(self):
        class CrashStrategy(BaseStrategy):
            def analyze(self, candles): raise Exception("Boom")
        
        s1 = MockStrategy("S1", Direction.CALL, 0.8)
        s2 = CrashStrategy("C1", Direction.CALL, 0.8) # Error handled internally
        consensus = SignalConsensus(strategies=[s1, s2], min_agreement=0.5)
        res = consensus.evaluate(np.zeros((10, 5)))
        self.assertEqual(res.direction, Direction.CALL)
        self.assertEqual(len(res.participating), 1)

if __name__ == '__main__':
    unittest.main()

