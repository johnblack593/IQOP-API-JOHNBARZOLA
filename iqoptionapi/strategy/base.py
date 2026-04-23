"""
iqoptionapi/strategy/base.py
─────────────────────────────
Clase base abstracta para todas las estrategias de JCBV-NEXUS.
Toda estrategia DEBE heredar de BaseStrategy e implementar analyze().
"""
from __future__ import annotations
import abc
import numpy as np
from numpy.typing import NDArray
from typing import Optional
from iqoptionapi.strategy.signal import Signal, Direction, AssetType


class BaseStrategy(abc.ABC):
    """
    Clase base para estrategias de trading.

    Subclases deben implementar:
      - analyze(candles) → Signal

    Subclases pueden sobreescribir:
      - name (property) → str identificador único
      - min_candles (property) → int mínimo de velas requeridas
      - validate_candles(candles) → bool validación previa
    """

    def __init__(
        self,
        asset: str,
        asset_type: AssetType = AssetType.BINARY,
        duration: int = 60,
        amount: float = 1.0,
    ) -> None:
        """
        Args:
            asset:      Nombre del activo (ej: "EURUSD")
            asset_type: Tipo de instrumento
            duration:   Duración en segundos (60, 120, 300...)
            amount:     Monto en USD por operación (> 0)
        """
        if amount <= 0:
            raise ValueError(f"amount debe ser > 0, recibido: {amount}")
        self._asset = asset
        self._asset_type = asset_type
        self._duration = duration
        self._amount = amount

    @property
    def name(self) -> str:
        """Identificador único de la estrategia. Por defecto: nombre de clase."""
        return self.__class__.__name__

    @property
    def min_candles(self) -> int:
        """
        Número mínimo de velas requeridas para analyze().
        Las subclases DEBEN sobreescribir este valor.
        """
        return 1

    def validate_candles(self, candles: NDArray[np.float64]) -> bool:
        """
        Valida que el array de velas tenga suficientes datos.
        Las subclases pueden sobreescribir para validaciones adicionales.

        Args:
            candles: array shape (N, 5) → [open, high, low, close, volume]

        Returns:
            True si los datos son válidos para analyze()
        """
        if candles is None or len(candles) < self.min_candles:
            return False
        if candles.ndim != 2 or candles.shape[1] < 4:
            return False
        return True

    @abc.abstractmethod
    def analyze(self, candles: NDArray[np.float64]) -> Signal:
        """
        Analiza las velas y retorna una señal de trading.

        Args:
            candles: array shape (N, 5) → [open, high, low, close, volume]
                     ordenado de más antiguo (índice 0) a más reciente (índice -1)

        Returns:
            Signal con direction=HOLD si no hay señal clara.
            NUNCA retornar None — siempre retornar un Signal.
        """

    def _hold(self, confidence: float = 0.0, metadata: dict | None = None) -> Signal:
        """
        Helper para retornar HOLD limpiamente.
        Las subclases usan self._hold() en lugar de construir Signal manualmente.
        """
        return Signal(
            asset=self._asset,
            direction=Direction.HOLD,
            duration=self._duration,
            amount=self._amount,
            asset_type=self._asset_type,
            confidence=confidence,
            strategy_id=self.name,
            metadata=metadata or {},
        )

    def _signal(
        self,
        direction: Direction,
        confidence: float,
        metadata: dict | None = None,
    ) -> Signal:
        """
        Helper para retornar CALL o PUT limpiamente.
        """
        return Signal(
            asset=self._asset,
            direction=direction,
            duration=self._duration,
            amount=self._amount,
            asset_type=self._asset_type,
            confidence=confidence,
            strategy_id=self.name,
            metadata=metadata or {},
        )
