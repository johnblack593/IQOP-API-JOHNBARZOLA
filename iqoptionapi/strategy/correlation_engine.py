"""
CorrelationEngine — correlación de Pearson entre activos usando candle_cache.
El robot evita operar activos altamente correlacionados simultáneamente.
READ-ONLY: nunca modifica estado de la API.
"""
import math
from iqoptionapi.logger import get_logger


class CorrelationEngine:
    def __init__(self, candle_cache):
        self._cache = candle_cache
        self._logger = get_logger(__name__)

    def get_correlation(self, active_a: int, active_b: int, size: int, n: int = 30) -> float:
        """
        Correlación de Pearson entre los cierres de las últimas n velas.
        Retorna 0.0 si < 5 velas en algún activo.
        """
        candles_a = self._cache.get_candles(active_a, size, n)
        candles_b = self._cache.get_candles(active_b, size, n)

        closes_a: list[float] = []
        for c in candles_a:
            v = c.get("close")
            if v is not None:
                try:
                    closes_a.append(float(v))
                except (TypeError, ValueError):
                    continue

        closes_b: list[float] = []
        for c in candles_b:
            v = c.get("close")
            if v is not None:
                try:
                    closes_b.append(float(v))
                except (TypeError, ValueError):
                    continue

        # Align to shortest
        min_len = min(len(closes_a), len(closes_b))
        if min_len < 5:
            return 0.0

        return self._pearson(closes_a[:min_len], closes_b[:min_len])

    def get_correlated_assets(
        self, active_id: int, candidate_ids: list[int],
        size: int, threshold: float = 0.8, n: int = 30,
    ) -> list[int]:
        """Retorna candidatos con correlación >= threshold con active_id."""
        result: list[int] = []
        for cid in candidate_ids:
            if cid == active_id:
                continue
            corr = self.get_correlation(active_id, cid, size, n)
            if abs(corr) >= threshold:
                result.append(cid)
        return result

    def get_correlation_matrix(
        self, active_ids: list[int], size: int, n: int = 30,
    ) -> dict[tuple[int, int], float]:
        """Calcula correlación entre todos los pares únicos."""
        matrix: dict[tuple[int, int], float] = {}
        for i in range(len(active_ids)):
            for j in range(i + 1, len(active_ids)):
                a, b = active_ids[i], active_ids[j]
                matrix[(a, b)] = self.get_correlation(a, b, size, n)
        return matrix

    def _pearson(self, xs: list[float], ys: list[float]) -> float:
        n = len(xs)
        if n < 5:
            return 0.0
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
        den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
        if den_x == 0 or den_y == 0:
            return 0.0
        return num / (den_x * den_y)
