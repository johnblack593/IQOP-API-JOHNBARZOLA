"""
iqoptionapi/strategy/registry.py
──────────────────────────────────
Registry de estrategias. Permite registrar y recuperar
estrategias por nombre sin imports directos.

Uso:
    from iqoptionapi.strategy.registry import StrategyRegistry

    @StrategyRegistry.register
    class MyStrategy(BaseStrategy):
        ...

    strat = StrategyRegistry.get("MyStrategy")(asset="EURUSD")
"""
from __future__ import annotations
from typing import Type
from iqoptionapi.strategy.base import BaseStrategy


class StrategyRegistry:
    _registry: dict[str, Type[BaseStrategy]] = {}

    @classmethod
    def register(cls, strategy_cls: Type[BaseStrategy]) -> Type[BaseStrategy]:
        """
        Decorador que registra una estrategia por su nombre.
        Uso: @StrategyRegistry.register
        Lanza ValueError si el nombre ya está registrado.
        """
        name = strategy_cls.__name__
        if name in cls._registry:
            raise ValueError(
                f"Estrategia '{name}' ya registrada. "
                "Usa un nombre de clase único."
            )
        cls._registry[name] = strategy_cls
        return strategy_cls

    @classmethod
    def get(cls, name: str) -> Type[BaseStrategy]:
        """
        Recupera la clase de estrategia por nombre.
        Lanza KeyError si no está registrada.
        """
        if name not in cls._registry:
            raise KeyError(
                f"Estrategia '{name}' no encontrada. "
                f"Registradas: {list(cls._registry.keys())}"
            )
        return cls._registry[name]

    @classmethod
    def list_all(cls) -> list[str]:
        """Lista los nombres de todas las estrategias registradas."""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """
        Limpia el registry. SOLO para uso en tests.
        NO llamar en código de producción.
        """
        cls._registry.clear()
