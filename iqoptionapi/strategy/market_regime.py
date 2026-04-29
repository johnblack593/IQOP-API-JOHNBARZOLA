"""
MarketRegime — detecta si el mercado está en tendencia o rango usando ADX simplificado.
READ-ONLY: nunca modifica estado de la API.

Reglas de interpretación ADX:
  ADX > 25  → TRENDING
  ADX < 20  → RANGING
  20-25     → TRANSITIONING
"""
from typing import Literal
from iqoptionapi.logger import get_logger

RegimeType = Literal["trending", "ranging", "transitioning"]


class MarketRegime:
    def __init__(self, candle_cache):
        self._cache = candle_cache
        self._logger = get_logger(__name__)

    def get_adx(self, active_id: int, size: int, period: int = 14) -> float:
        """ADX simplificado. Retorna -1.0 si datos insuficientes."""
        required = period * 2
        candles = self._cache.get_candles(active_id, size, required + 10)
        if len(candles) < required:
            return -1.0
        candles = list(reversed(candles))
        highs, lows, closes = [], [], []
        for c in candles:
            try:
                highs.append(float(c.get("max", 0)))
                lows.append(float(c.get("min", 0)))
                closes.append(float(c.get("close", 0)))
            except (TypeError, ValueError):
                return -1.0
        n = len(highs)
        if n < required:
            return -1.0
        tr_list, plus_dm_list, minus_dm_list = [], [], []
        for i in range(1, n):
            hl = highs[i] - lows[i]
            hpc = abs(highs[i] - closes[i - 1])
            lpc = abs(lows[i] - closes[i - 1])
            tr_list.append(max(hl, hpc, lpc))
            up = highs[i] - highs[i - 1]
            dn = lows[i - 1] - lows[i]
            plus_dm_list.append(up if (up > dn and up > 0) else 0.0)
            minus_dm_list.append(dn if (dn > up and dn > 0) else 0.0)
        if len(tr_list) < period:
            return -1.0

        def ws(data, p):
            if len(data) < p:
                return []
            s = [sum(data[:p])]
            for i in range(p, len(data)):
                s.append(s[-1] - s[-1] / p + data[i])
            return s

        s_tr = ws(tr_list, period)
        s_pdm = ws(plus_dm_list, period)
        s_mdm = ws(minus_dm_list, period)
        if not s_tr:
            return -1.0
        ml = min(len(s_tr), len(s_pdm), len(s_mdm))
        dx_list = []
        for i in range(ml):
            if s_tr[i] == 0:
                continue
            pdi = (s_pdm[i] / s_tr[i]) * 100
            mdi = (s_mdm[i] / s_tr[i]) * 100
            ds = pdi + mdi
            dx_list.append(abs(pdi - mdi) / ds * 100 if ds else 0.0)
        if len(dx_list) < period:
            return -1.0
        adx_s = ws(dx_list, period)
        if not adx_s:
            return -1.0
        val = adx_s[-1] if len(adx_s) > 1 else adx_s[-1] / period
        return round(max(0.0, min(100.0, val)), 2)

    def get_regime(self, active_id: int, size: int, period: int = 14) -> RegimeType:
        """Retorna régimen. 'transitioning' si datos insuficientes."""
        adx = self.get_adx(active_id, size, period)
        if adx < 0:
            return "transitioning"
        if adx > 25:
            return "trending"
        if adx < 20:
            return "ranging"
        return "transitioning"

    def get_trend_direction(self, active_id: int, size: int, period: int = 14) -> Literal["up", "down", "neutral"]:
        """+DI > -DI → 'up', -DI > +DI → 'down', else 'neutral'."""
        if self.get_regime(active_id, size, period) != "trending":
            return "neutral"
        required = period * 2
        candles = self._cache.get_candles(active_id, size, required + 10)
        if len(candles) < required:
            return "neutral"
        candles = list(reversed(candles))
        highs, lows, closes = [], [], []
        for c in candles:
            try:
                highs.append(float(c.get("max", 0)))
                lows.append(float(c.get("min", 0)))
                closes.append(float(c.get("close", 0)))
            except (TypeError, ValueError):
                return "neutral"
        n = len(highs)
        pdm, mdm, trs = 0.0, 0.0, 0.0
        lb = min(period, n - 1)
        for i in range(n - lb, n):
            hl = highs[i] - lows[i]
            hpc = abs(highs[i] - closes[i - 1])
            lpc = abs(lows[i] - closes[i - 1])
            trs += max(hl, hpc, lpc)
            up = highs[i] - highs[i - 1]
            dn = lows[i - 1] - lows[i]
            if up > dn and up > 0:
                pdm += up
            if dn > up and dn > 0:
                mdm += dn
        if trs == 0:
            return "neutral"
        if pdm / trs > mdm / trs:
            return "up"
        if mdm / trs > pdm / trs:
            return "down"
        return "neutral"

    def get_summary(self, active_id: int, size: int) -> dict:
        """Retorna: {adx, regime, trend_direction, n_candles_used, is_reliable}"""
        period = 14
        candles = self._cache.get_candles(active_id, size)
        n = len(candles)
        return {
            "adx": self.get_adx(active_id, size, period),
            "regime": self.get_regime(active_id, size, period),
            "trend_direction": self.get_trend_direction(active_id, size, period),
            "n_candles_used": n,
            "is_reliable": n >= period * 2,
        }
