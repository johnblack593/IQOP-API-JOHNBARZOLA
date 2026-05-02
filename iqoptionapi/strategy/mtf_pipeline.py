"""
iqoptionapi/strategy/mtf_pipeline.py
──────────────────────────────────────
Pipeline de indicadores técnicos multi-timeframe.
Calcula indicadores locales desde CandleCache en M1, M5 y M15.
"""
from __future__ import annotations
import logging
import numpy as np
from typing import TYPE_CHECKING

from iqoptionapi.strategy.mtf_snapshot import MTFSnapshot, TimeframeIndicators
from iqoptionapi.strategy import indicators as ind

if TYPE_CHECKING:
    from iqoptionapi.candle_cache import CandleCache

logger = logging.getLogger(__name__)

# Timeframes estándar para opciones binarias IQ Option
MTF_TIMEFRAMES: dict[str, int] = {
    "m1":  60,
    "m5":  300,
    "m15": 900,
}

# Velas mínimas recomendadas para que los indicadores sean útiles
MIN_CANDLES: int = 35   # cubre RSI(14) + MACD(26+9)


class MTFPipeline:
    """
    Calcula indicadores técnicos locales en múltiples timeframes
    desde CandleCache y retorna un MTFSnapshot consolidado.

    Uso:
        pipeline = MTFPipeline(candle_cache)
        snapshot = pipeline.compute(active_id=1, asset="EURUSD")

        if snapshot.multi_tf_bias == 'CALL':
            # al menos 2 de 3 timeframes apuntan arriba
            ...
    """

    def __init__(
        self,
        candle_cache: "CandleCache",
        candle_history: int = 100,
    ) -> None:
        """
        Args:
            candle_cache:    Instancia compartida de CandleCache.
            candle_history:  Velas a solicitar por timeframe (default 100).
        """
        self._cache = candle_cache
        self._candle_history = candle_history

    def compute(self, active_id: int, asset: str) -> MTFSnapshot:
        """
        Calcula indicadores para M1, M5 y M15 del activo dado.

        Args:
            active_id: ID numérico del activo en IQ Option.
            asset:     Nombre del activo (ej: "EURUSD") — solo para el snapshot.

        Returns:
            MTFSnapshot con los indicadores de cada timeframe.
            Los timeframes sin velas retornan TimeframeIndicators con nan.
        """
        m1  = self._compute_tf(active_id, MTF_TIMEFRAMES["m1"])
        m5  = self._compute_tf(active_id, MTF_TIMEFRAMES["m5"])
        m15 = self._compute_tf(active_id, MTF_TIMEFRAMES["m15"])

        snapshot = MTFSnapshot(asset=asset, m1=m1, m5=m5, m15=m15)

        logger.debug(
            "MTFPipeline.compute: asset=%s available_tf=%s bias=%s",
            asset, snapshot.available_timeframes, snapshot.multi_tf_bias
        )
        return snapshot

    def _compute_tf(
        self, active_id: int, size: int
    ) -> TimeframeIndicators:
        """Calcula todos los indicadores para un único timeframe."""
        candles = self._cache.get_candles(active_id, size, n=self._candle_history)
        n = len(candles)

        if n < MIN_CANDLES:
            logger.debug(
                "MTFPipeline: insufficient candles for active_id=%s size=%s "
                "(got %d, need %d)",
                active_id, size, n, MIN_CANDLES
            )
            return TimeframeIndicators(timeframe=size, candles_used=n)

        # Extraer arrays desde los dicts del cache
        # CandleCache.get_candles retorna velas más recientes primero
        # → invertir para que el índice 0 sea la vela más antigua
        closes = np.array(
            [c["close"] for c in reversed(candles)], dtype=np.float64
        )
        highs  = np.array(
            [c["max"]  for c in reversed(candles)], dtype=np.float64
        )
        lows   = np.array(
            [c["min"]  for c in reversed(candles)], dtype=np.float64
        )

        # Calcular todos los indicadores
        _sma20          = ind.sma(closes, 20)
        _ema20          = ind.ema(closes, 20)
        _rsi14          = ind.rsi(closes, 14)
        _macd, _ms, _mh = ind.macd(closes)
        _bbu, _bbm, _bbl = ind.bollinger_bands(closes, 20)
        _stk, _std      = ind.stochastic(highs, lows, closes)
        _atr14          = ind.atr(highs, lows, closes, 14)

        return TimeframeIndicators(
            timeframe=size,
            candles_used=n,
            sma_20=_sma20,
            ema_20=_ema20,
            rsi_14=_rsi14,
            macd_line=_macd,
            macd_signal=_ms,
            macd_hist=_mh,
            bb_upper=_bbu,
            bb_mid=_bbm,
            bb_lower=_bbl,
            stoch_k=_stk,
            stoch_d=_std,
            atr_14=_atr14,
        )
