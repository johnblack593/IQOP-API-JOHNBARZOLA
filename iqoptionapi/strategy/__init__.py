"""
iqoptionapi/strategy
─────────────────────
Signal Engine de JCBV-NEXUS.

Exports públicos:
  BaseStrategy   — clase base para estrategias
  Signal         — dataclass de señal de trading
  Direction      — enum CALL/PUT/HOLD
  AssetType      — enum de tipos de instrumento
  StrategyRegistry — registro de estrategias
"""
from iqoptionapi.strategy.base import BaseStrategy
from iqoptionapi.strategy.signal import Signal, Direction, AssetType
from iqoptionapi.strategy.registry import StrategyRegistry
from iqoptionapi.strategy.pattern_engine import PatternEngine
from iqoptionapi.strategy.signal_consensus import SignalConsensus
from iqoptionapi.strategy.correlation_engine import CorrelationEngine
from iqoptionapi.strategy.market_regime import MarketRegime
from iqoptionapi.strategy.market_quality import MarketQualityMonitor

# Auto-registrar estrategias incluidas
from iqoptionapi.strategy.strategies import rsi_ema  # noqa: F401

__all__ = [
    "BaseStrategy",
    "Signal",
    "Direction",
    "AssetType",
    "StrategyRegistry",
    "PatternEngine",
    "SignalConsensus",
    "CorrelationEngine",
    "MarketRegime",
    "MarketQualityMonitor",
]
