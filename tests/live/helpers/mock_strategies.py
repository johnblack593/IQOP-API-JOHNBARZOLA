"""
tests/live/helpers/mock_strategies.py
──────────────────────────────────────
Estrategias mock para validación de consenso y backtest.
"""
import numpy as np
from numpy.typing import NDArray
from iqoptionapi.strategy.base import BaseStrategy
from iqoptionapi.strategy.signal import Signal, Direction

class MockBuyStrategy(BaseStrategy):
    """Estrategia que siempre retorna BUY."""
    @property
    def min_candles(self) -> int:
        return 1

    def analyze(self, candles: NDArray[np.float64]) -> Signal:
        return self._signal(Direction.CALL, confidence=0.85)

class MockSellStrategy(BaseStrategy):
    """Estrategia que siempre retorna SELL."""
    @property
    def min_candles(self) -> int:
        return 1

    def analyze(self, candles: NDArray[np.float64]) -> Signal:
        return self._signal(Direction.PUT, confidence=0.80)

class MockAlternatingStrategy(BaseStrategy):
    """Estrategia que alterna señales basado en el índice de la vela."""
    @property
    def min_candles(self) -> int:
        return 2

    def analyze(self, candles: NDArray[np.float64]) -> Signal:
        # Usamos el timestamp de la última vela para decidir
        last_ts = int(candles[-1, 0])
        if last_ts % 2 == 0:
            return self._signal(Direction.CALL, confidence=0.75)
        return self._signal(Direction.PUT, confidence=0.75)
