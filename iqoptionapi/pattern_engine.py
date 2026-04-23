"""
PatternEngine — detecta patrones de velas japonesas en el buffer de candle_cache.
Los robots consumen PatternSignal como señal de entrada.
READ-ONLY: nunca modifica estado de la API.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass
class PatternSignal:
    pattern: str                          # "DOJI", "HAMMER", etc.
    direction: Literal["call", "put", "neutral"]
    strength: float                       # 0.0 a 1.0
    candle_index: int                     # índice de la vela donde se detectó (0 = última)


class PatternEngine:
    def __init__(self, candle_cache):
        self._cache = candle_cache

    def detect(
        self,
        active_id: int,
        size: int,
        n_candles: int = 10,
    ) -> list[PatternSignal]:
        """
        Detecta todos los patrones activos en las últimas n_candles velas.
        Retorna lista vacía si no hay datos o < 2 velas.
        """
        candles = self._cache.get_candles(active_id, size, n_candles)
        if len(candles) < 2:
            return []

        signals: list[PatternSignal] = []

        for i, candle in enumerate(candles):
            # --- Single-candle patterns ---
            doji_str = self._is_doji(candle)
            if doji_str > 0.0:
                signals.append(PatternSignal(
                    pattern="DOJI",
                    direction="neutral",
                    strength=doji_str,
                    candle_index=i,
                ))

            hammer_str = self._is_hammer(candle)
            if hammer_str > 0.0:
                signals.append(PatternSignal(
                    pattern="HAMMER",
                    direction="call",
                    strength=hammer_str,
                    candle_index=i,
                ))

            star_str = self._is_shooting_star(candle)
            if star_str > 0.0:
                signals.append(PatternSignal(
                    pattern="SHOOTING_STAR",
                    direction="put",
                    strength=star_str,
                    candle_index=i,
                ))

            # --- Two-candle patterns (need previous) ---
            if i + 1 < len(candles):
                prev = candles[i + 1]  # candles[0] = más reciente

                bull_eng = self._is_bullish_engulfing(prev, candle)
                if bull_eng > 0.0:
                    signals.append(PatternSignal(
                        pattern="BULLISH_ENGULFING",
                        direction="call",
                        strength=bull_eng,
                        candle_index=i,
                    ))

                bear_eng = self._is_bearish_engulfing(prev, candle)
                if bear_eng > 0.0:
                    signals.append(PatternSignal(
                        pattern="BEARISH_ENGULFING",
                        direction="put",
                        strength=bear_eng,
                        candle_index=i,
                    ))

                inside = self._is_inside_bar(prev, candle)
                if inside > 0.0:
                    signals.append(PatternSignal(
                        pattern="INSIDE_BAR",
                        direction="neutral",
                        strength=inside,
                        candle_index=i,
                    ))

        return signals

    # --- Detectores individuales (privados) ---

    def _is_doji(self, candle: dict) -> float:
        """
        |open - close| < 0.1 * (max - min)
        Retorna strength 0.0-1.0 (qué tan perfecto es el doji)
        """
        c_open = candle.get("open")
        c_close = candle.get("close")
        c_max = candle.get("max")
        c_min = candle.get("min")
        if c_open is None or c_close is None or c_max is None or c_min is None:
            return 0.0

        try:
            c_open, c_close = float(c_open), float(c_close)
            c_max, c_min = float(c_max), float(c_min)
        except (TypeError, ValueError):
            return 0.0

        full_range = c_max - c_min
        if full_range <= 0:
            return 0.0

        body = abs(c_open - c_close)
        ratio = body / full_range

        if ratio >= 0.1:
            return 0.0

        # Cuanto más pequeño el ratio, más perfecto el doji
        return round(1.0 - (ratio / 0.1), 4)

    def _is_hammer(self, candle: dict) -> float:
        """
        lower_wick > 2 * body, upper_wick < 0.3 * body
        Señal: "call"
        """
        c_open = candle.get("open")
        c_close = candle.get("close")
        c_max = candle.get("max")
        c_min = candle.get("min")
        if c_open is None or c_close is None or c_max is None or c_min is None:
            return 0.0

        try:
            c_open, c_close = float(c_open), float(c_close)
            c_max, c_min = float(c_max), float(c_min)
        except (TypeError, ValueError):
            return 0.0

        body = abs(c_open - c_close)
        if body <= 0:
            return 0.0

        upper_wick = c_max - max(c_open, c_close)
        lower_wick = min(c_open, c_close) - c_min

        if lower_wick <= 2 * body:
            return 0.0
        if upper_wick > 0.3 * body:
            return 0.0

        # Strength: qué tan larga es la mecha inferior vs body
        strength = min(1.0, (lower_wick / body - 2.0) / 3.0)
        return round(max(0.0, strength), 4)

    def _is_shooting_star(self, candle: dict) -> float:
        """
        upper_wick > 2 * body, lower_wick < 0.3 * body
        Señal: "put"
        """
        c_open = candle.get("open")
        c_close = candle.get("close")
        c_max = candle.get("max")
        c_min = candle.get("min")
        if c_open is None or c_close is None or c_max is None or c_min is None:
            return 0.0

        try:
            c_open, c_close = float(c_open), float(c_close)
            c_max, c_min = float(c_max), float(c_min)
        except (TypeError, ValueError):
            return 0.0

        body = abs(c_open - c_close)
        if body <= 0:
            return 0.0

        upper_wick = c_max - max(c_open, c_close)
        lower_wick = min(c_open, c_close) - c_min

        if upper_wick <= 2 * body:
            return 0.0
        if lower_wick > 0.3 * body:
            return 0.0

        strength = min(1.0, (upper_wick / body - 2.0) / 3.0)
        return round(max(0.0, strength), 4)

    def _is_bullish_engulfing(self, prev: dict, curr: dict) -> float:
        """
        curr.open < prev.close AND curr.close > prev.open (vela alcista envuelve bajista)
        Señal: "call"
        """
        try:
            p_open = float(prev.get("open", 0))
            p_close = float(prev.get("close", 0))
            c_open = float(curr.get("open", 0))
            c_close = float(curr.get("close", 0))
        except (TypeError, ValueError):
            return 0.0

        # Previous must be bearish, current must be bullish
        if p_close >= p_open:
            return 0.0
        if c_close <= c_open:
            return 0.0

        # Engulfing condition
        if c_open < p_close and c_close > p_open:
            prev_body = abs(p_open - p_close)
            curr_body = abs(c_close - c_open)
            if prev_body <= 0:
                return 0.0
            ratio = curr_body / prev_body
            strength = min(1.0, (ratio - 1.0) / 2.0)
            return round(max(0.0, strength), 4)

        return 0.0

    def _is_bearish_engulfing(self, prev: dict, curr: dict) -> float:
        """
        curr.open > prev.close AND curr.close < prev.open
        Señal: "put"
        """
        try:
            p_open = float(prev.get("open", 0))
            p_close = float(prev.get("close", 0))
            c_open = float(curr.get("open", 0))
            c_close = float(curr.get("close", 0))
        except (TypeError, ValueError):
            return 0.0

        # Previous must be bullish, current must be bearish
        if p_close <= p_open:
            return 0.0
        if c_close >= c_open:
            return 0.0

        # Engulfing condition
        if c_open > p_close and c_close < p_open:
            prev_body = abs(p_close - p_open)
            curr_body = abs(c_open - c_close)
            if prev_body <= 0:
                return 0.0
            ratio = curr_body / prev_body
            strength = min(1.0, (ratio - 1.0) / 2.0)
            return round(max(0.0, strength), 4)

        return 0.0

    def _is_inside_bar(self, prev: dict, curr: dict) -> float:
        """
        curr.max < prev.max AND curr.min > prev.min
        Señal: "neutral" (breakout pendiente)
        """
        try:
            p_max = float(prev.get("max", 0))
            p_min = float(prev.get("min", 0))
            c_max = float(curr.get("max", 0))
            c_min = float(curr.get("min", 0))
        except (TypeError, ValueError):
            return 0.0

        if c_max < p_max and c_min > p_min:
            prev_range = p_max - p_min
            curr_range = c_max - c_min
            if prev_range <= 0:
                return 0.0
            # Smaller current range relative to prev = stronger inside bar
            ratio = 1.0 - (curr_range / prev_range)
            return round(max(0.0, min(1.0, ratio)), 4)

        return 0.0
