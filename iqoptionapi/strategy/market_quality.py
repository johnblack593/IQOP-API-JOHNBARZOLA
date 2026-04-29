"""
MarketQualityMonitor — detecta activos con spread anormal.
Los robots deben consultar is_tradeable() antes de abrir cualquier posición.
READ-ONLY: nunca modifica estado de la API.
"""
from iqoptionapi.logger import get_logger


class MarketQualityMonitor:
    def __init__(self, candle_cache):
        self._cache = candle_cache
        self._logger = get_logger(__name__)

    def get_spread(self, active_id: int, size: int, n: int = 10) -> float:
        """
        Spread promedio de las últimas n velas.
        Si hay campos ask/bid: usa ask - bid.
        Si no: usa (max - min) / open como proxy de spread normalizado.
        Retorna 0.0 si no hay datos suficientes.
        """
        candles = self._cache.get_candles(active_id, size, n)
        if not candles:
            return 0.0

        spreads: list[float] = []
        for c in candles:
            ask = c.get("ask")
            bid = c.get("bid")
            if ask is not None and bid is not None:
                # Spread directo ask - bid
                try:
                    spreads.append(float(ask) - float(bid))
                except (TypeError, ValueError):
                    continue
            else:
                # Proxy: (max - min) / open
                c_max = c.get("max")
                c_min = c.get("min")
                c_open = c.get("open")
                if c_max is None or c_min is None or c_open is None:
                    continue
                try:
                    c_max = float(c_max)
                    c_min = float(c_min)
                    c_open = float(c_open)
                except (TypeError, ValueError):
                    continue
                if c_open == 0:
                    continue
                spreads.append((c_max - c_min) / c_open)

        if not spreads:
            return 0.0

        return sum(spreads) / len(spreads)

    def is_tradeable(
        self,
        active_id: int,
        size: int,
        max_spread: float = 0.001,
    ) -> bool:
        """
        True si el spread actual está dentro del umbral aceptable.
        El robot llama esto antes de cada operación.
        Retorna True si no hay datos (fail-open, no bloquea el robot).
        """
        candles = self._cache.get_candles(active_id, size, 1)
        if not candles:
            return True  # fail-open

        spread = self.get_spread(active_id, size, n=10)
        return spread <= max_spread

    def get_quality_score(self, active_id: int, size: int) -> float:
        """
        Score 0.0 (mala calidad) a 1.0 (calidad perfecta).
        Basado en: spread normalizado + consistencia de volumen de las últimas 20 velas.
        Si no hay datos suficientes (< 5 velas) → retorna 0.5 (neutral).
        """
        candles = self._cache.get_candles(active_id, size, 20)
        if len(candles) < 5:
            return 0.5

        # --- Componente 1: spread normalizado (peso 0.6) ---
        spread = self.get_spread(active_id, size, n=len(candles))
        # Mapear spread a score: 0 spread = 1.0, spread >= 0.01 = 0.0
        spread_score = max(0.0, 1.0 - (spread / 0.01))

        # --- Componente 2: consistencia de volumen (peso 0.4) ---
        volumes: list[float] = []
        for c in candles:
            vol = c.get("volume")
            if vol is not None:
                try:
                    volumes.append(float(vol))
                except (TypeError, ValueError):
                    continue

        if len(volumes) >= 5:
            mean_vol = sum(volumes) / len(volumes)
            if mean_vol > 0:
                # Coeficiente de variación: desviación estándar / media
                variance = sum((v - mean_vol) ** 2 for v in volumes) / len(volumes)
                std_vol = variance ** 0.5
                cv = std_vol / mean_vol
                # CV bajo = volumen consistente = alta calidad
                vol_score = max(0.0, 1.0 - cv)
            else:
                vol_score = 0.5
        else:
            # Sin datos de volumen, asumimos neutral
            vol_score = 0.5

        score = (spread_score * 0.6) + (vol_score * 0.4)
        return max(0.0, min(1.0, round(score, 4)))

    def get_summary(self, active_id: int, size: int) -> dict:
        """
        Retorna dict con: {spread, quality_score, is_tradeable, n_candles_analyzed}
        Útil para logging y dashboards del robot.
        """
        candles = self._cache.get_candles(active_id, size)
        n_candles = len(candles)

        return {
            "spread": self.get_spread(active_id, size),
            "quality_score": self.get_quality_score(active_id, size),
            "is_tradeable": self.is_tradeable(active_id, size),
            "n_candles_analyzed": n_candles,
        }
