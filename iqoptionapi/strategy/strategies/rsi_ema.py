"""
iqoptionapi/strategy/strategies/rsi_ema.py
───────────────────────────────────────────
Estrategia de ejemplo: RSI sobrevendido/sobrecomprado
combinado con cruce de EMA rápida/lenta.

Señal CALL cuando:
  - RSI < RSI_OVERSOLD (30 por defecto)
  - EMA rápida cruza hacia arriba la EMA lenta

Señal PUT cuando:
  - RSI > RSI_OVERBOUGHT (70 por defecto)
  - EMA rápida cruza hacia abajo la EMA lenta

Confianza = distancia normalizada del RSI al umbral
  (RSI=20 con umbral 30 → confianza más alta que RSI=28)

ADVERTENCIA: Estrategia de demostración. NO usar en producción
con dinero real sin backtesting riguroso.
"""
import numpy as np
from numpy.typing import NDArray
from iqoptionapi.strategy.base import BaseStrategy
from iqoptionapi.strategy.signal import Signal, Direction, AssetType
from iqoptionapi.strategy.indicators import rsi, ema
from iqoptionapi.strategy.registry import StrategyRegistry


@StrategyRegistry.register
class RSIEMAStrategy(BaseStrategy):

    RSI_PERIOD:     int   = 14
    EMA_FAST:       int   = 9
    EMA_SLOW:       int   = 21
    RSI_OVERSOLD:   float = 30.0
    RSI_OVERBOUGHT: float = 70.0

    @property
    def min_candles(self) -> int:
        return max(self.RSI_PERIOD + 1, self.EMA_SLOW) + 2

    def analyze(self, candles: NDArray[np.float64]) -> Signal:
        if not self.validate_candles(candles):
            return self._hold(metadata={"reason": "insufficient_data"})

        closes = candles[:, 3].astype(np.float64)

        rsi_val      = rsi(closes, self.RSI_PERIOD)
        ema_fast_now = ema(closes, self.EMA_FAST)
        ema_slow_now = ema(closes, self.EMA_SLOW)
        ema_fast_prev = ema(closes[:-1], self.EMA_FAST)
        ema_slow_prev = ema(closes[:-1], self.EMA_SLOW)

        # Cualquier nan → sin señal
        if any(np.isnan(v) for v in [
            rsi_val, ema_fast_now, ema_slow_now,
            ema_fast_prev, ema_slow_prev
        ]):
            return self._hold(metadata={"reason": "nan_indicator"})

        crossed_up   = ema_fast_prev < ema_slow_prev and ema_fast_now >= ema_slow_now
        crossed_down = ema_fast_prev > ema_slow_prev and ema_fast_now <= ema_slow_now

        meta = {
            "rsi": round(rsi_val, 2),
            "ema_fast": round(ema_fast_now, 5),
            "ema_slow": round(ema_slow_now, 5),
        }

        if rsi_val < self.RSI_OVERSOLD and crossed_up:
            confidence = min(1.0, (self.RSI_OVERSOLD - rsi_val) / self.RSI_OVERSOLD)
            return self._signal(Direction.CALL, round(confidence, 3), meta)

        if rsi_val > self.RSI_OVERBOUGHT and crossed_down:
            confidence = min(1.0, (rsi_val - self.RSI_OVERBOUGHT) / (100.0 - self.RSI_OVERBOUGHT))
            return self._signal(Direction.PUT, round(confidence, 3), meta)

        return self._hold(metadata=meta)
