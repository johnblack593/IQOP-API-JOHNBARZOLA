"""
iqoptionapi/strategy/server_indicator_bridge.py
────────────────────────────────────────────────
Normalizador de indicadores técnicos del servidor IQ Option.
"""

import logging
from typing import Optional, List, Any
from iqoptionapi.strategy.signal import Direction


class ServerIndicatorBridge:
    """
    Bridge para parsear y normalizar el dict de indicadores del servidor.
    Proporciona una interfaz limpia para consultar señales y valores numéricos.
    """

    def __init__(self, raw: Optional[dict] = None) -> None:
        """
        Args:
            raw: El dict retornado por get_technical_indicators().
        """
        self._raw = raw or {}
        self._logger = logging.getLogger(__name__)

    def is_empty(self) -> bool:
        """Retorna True si el bridge no contiene datos válidos del servidor."""
        if not self._raw:
            return True

        # El servidor a veces retorna un error explícito en el dict
        if self._raw.get("code") == "no_technical_indicator_available":
            return True

        return False

    def get_signal(self, indicator: str) -> Optional[Direction]:
        """
        Retorna la dirección sugerida por el indicador especificado.
        BUY -> Direction.CALL, SELL -> Direction.PUT, NEUTRAL -> Direction.HOLD.
        """
        if self.is_empty():
            return None

        data = self._raw.get(indicator.lower())
        if not isinstance(data, dict):
            return None

        sig_str = str(data.get("signal", "")).upper()

        if sig_str == "BUY":
            return Direction.CALL
        elif sig_str == "SELL":
            return Direction.PUT
        elif sig_str == "NEUTRAL":
            return Direction.HOLD

        return None

    def get_value(self, indicator: str, field: str = "value") -> Optional[float]:
        """
        Retorna el valor numérico de un campo específico de un indicador.
        Nunca lanza excepción, retorna None si el campo no existe o no es numérico.
        """
        if self.is_empty():
            return None

        data = self._raw.get(indicator.lower())
        if not isinstance(data, dict):
            return None

        val = data.get(field)
        if val is None:
            return None

        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def consensus_direction(self) -> Direction:
        """
        Retorna la dirección dominante basada en voting simple (BUY vs SELL).
        Retorna Direction.HOLD si hay empate o no hay indicadores.
        """
        if self.is_empty():
            return Direction.HOLD

        buy_votes = 0
        sell_votes = 0

        for _, data in self._raw.items():
            if not isinstance(data, dict):
                continue

            sig = str(data.get("signal", "")).upper()
            if sig == "BUY":
                buy_votes += 1
            elif sig == "SELL":
                sell_votes += 1

        if buy_votes > sell_votes:
            return Direction.CALL
        elif sell_votes > buy_votes:
            return Direction.PUT

        return Direction.HOLD

    def available_indicators(self) -> List[str]:
        """Lista de indicadores presentes en el dict crudo del servidor."""
        if self.is_empty():
            return []
        # Solo keys que contienen dicts (los indicadores)
        return [k for k, v in self._raw.items() if isinstance(v, dict)]

    def as_dict(self) -> dict[str, Any]:
        """
        Retorna una representación serializable y limpia del bridge.
        Incluye consenso, señales y valores numéricos filtrados.
        """
        try:
            available = self.available_indicators()
            signals = {}
            values = {}

            for ind in available:
                data = self._raw[ind]
                # Señal
                sig = data.get("signal")
                if sig:
                    signals[ind] = sig

                # Valores numéricos (filtramos 'signal' y convertimos a float)
                ind_values = {}
                for k, v in data.items():
                    if k == "signal":
                        continue
                    try:
                        ind_values[k] = float(v)
                    except (ValueError, TypeError):
                        continue

                if ind_values:
                    values[ind] = ind_values

            return {
                "available": available,
                "consensus": self.consensus_direction().name,
                "signals": signals,
                "values": values,
            }
        except Exception as e:
            self._logger.error("Error serializing ServerIndicatorBridge: %s", e)
            return {
                "available": [],
                "consensus": Direction.HOLD.name,
                "signals": {},
                "values": {},
            }
