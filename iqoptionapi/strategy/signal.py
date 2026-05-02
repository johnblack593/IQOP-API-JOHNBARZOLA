"""
iqoptionapi/strategy/signal.py
───────────────────────────────
Dataclass inmutable que representa una decisión de trading.
Una Signal es el OUTPUT de cualquier estrategia.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum



class Direction(str, Enum):
    """Dirección de la operación."""
    CALL = "call"   # precio sube
    PUT  = "put"    # precio baja
    HOLD = "hold"   # sin señal — no operar


class AssetType(str, Enum):
    """Tipo de activo soportado."""
    BINARY  = "binary-option"
    DIGITAL = "digital-option"
    TURBO   = "turbo-option"
    CFD     = "cfd"           # Margen: Forex, Acciones, Cripto, Índices, Fondos


@dataclass(frozen=True)
class Signal:
    """
    Representa una señal de trading generada por una estrategia.

    Atributos:
        asset:       Nombre del activo (ej: "EURUSD", "BTCUSD")
        direction:   CALL, PUT o HOLD
        duration:    Duración en segundos (60, 120, 300...)
        amount:      Monto en USD a invertir
        asset_type:  Tipo de instrumento
        confidence:  Confianza 0.0–1.0 (1.0 = señal máxima)
        strategy_id: Nombre de la estrategia que generó la señal
        timestamp:   Momento de generación (UTC)
        metadata:    Datos adicionales opcionales (indicadores, etc.)

    Una Signal con direction=HOLD NO debe ejecutarse.
    El campo confidence permite al circuit breaker filtrar señales débiles.
    """
    asset:       str
    direction:   Direction
    duration:    int
    amount:      float
    asset_type:  AssetType
    confidence:  float
    strategy_id: str
    timestamp:   datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata:    dict = field(default_factory=dict)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence debe estar entre 0.0 y 1.0, recibido: {self.confidence}"
            )
        if self.amount <= 0:
            raise ValueError(
                f"amount debe ser > 0, recibido: {self.amount}"
            )
        if self.duration < 0:
            raise ValueError(
                f"duration debe ser >= 0, recibido: {self.duration}"
            )

    @property
    def is_actionable(self) -> bool:
        """True si la señal debe ejecutarse (no es HOLD)."""
        return self.direction != Direction.HOLD
