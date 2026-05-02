"""
iqoptionapi/strategy/mtf_snapshot.py
──────────────────────────────────────
Snapshot inmutable de indicadores técnicos para un activo
en múltiples timeframes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import math


@dataclass(frozen=True)
class TimeframeIndicators:
    """
    Indicadores calculados para un solo timeframe.
    Todos los valores pueden ser float('nan') si los datos son insuficientes.
    """
    timeframe: int                       # en segundos: 60, 300, 900
    candles_used: int                    # cantidad de velas disponibles

    # Trend
    sma_20: float = float('nan')
    ema_20: float = float('nan')

    # Momentum
    rsi_14: float = float('nan')
    stoch_k: float = float('nan')
    stoch_d: float = float('nan')

    # Trend strength
    macd_line: float = float('nan')
    macd_signal: float = float('nan')
    macd_hist: float = float('nan')

    # Volatility
    bb_upper: float = float('nan')
    bb_mid: float = float('nan')
    bb_lower: float = float('nan')
    atr_14: float = float('nan')

    @property
    def has_data(self) -> bool:
        """True si al menos el RSI tiene valor válido."""
        return not math.isnan(self.rsi_14)

    @property
    def bias(self) -> str:
        """
        Sesgo direccional simplificado basado en RSI y MACD.
        Retorna 'CALL', 'PUT', o 'NEUTRAL'.
        """
        score = 0
        if not math.isnan(self.rsi_14):
            if self.rsi_14 < 40:
                score += 1      # oversold → CALL
            elif self.rsi_14 > 60:
                score -= 1      # overbought → PUT
        if not math.isnan(self.macd_hist):
            if self.macd_hist > 0:
                score += 1
            elif self.macd_hist < 0:
                score -= 1
        if score > 0:
            return 'CALL'
        elif score < 0:
            return 'PUT'
        return 'NEUTRAL'


@dataclass(frozen=True)
class MTFSnapshot:
    """
    Snapshot consolidado de indicadores técnicos en múltiples timeframes
    para un activo específico.
    """
    asset: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    m1:  Optional[TimeframeIndicators] = None   # 60s
    m5:  Optional[TimeframeIndicators] = None   # 300s
    m15: Optional[TimeframeIndicators] = None   # 900s

    @property
    def available_timeframes(self) -> list[int]:
        """Lista de timeframes con datos válidos."""
        result = []
        if self.m1 and self.m1.has_data:
            result.append(60)
        if self.m5 and self.m5.has_data:
            result.append(300)
        if self.m15 and self.m15.has_data:
            result.append(900)
        return result

    @property
    def multi_tf_bias(self) -> str:
        """
        Consenso direccional entre todos los timeframes disponibles.
        Retorna 'CALL', 'PUT' o 'NEUTRAL'.
        """
        votes = {'CALL': 0, 'PUT': 0, 'NEUTRAL': 0}
        for tf in [self.m1, self.m5, self.m15]:
            if tf and tf.has_data:
                votes[tf.bias] += 1
        if votes['CALL'] > votes['PUT']:
            return 'CALL'
        elif votes['PUT'] > votes['CALL']:
            return 'PUT'
        return 'NEUTRAL'
