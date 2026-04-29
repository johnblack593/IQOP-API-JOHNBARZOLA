"""
iqoptionapi/signal_consensus.py
───────────────────────────────
Combinador de señales de múltiples estrategias (Consenso M-de-N).
"""
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import numpy as np
from numpy.typing import NDArray
import logging
from iqoptionapi.strategy.base import BaseStrategy
from iqoptionapi.strategy.signal import Signal, Direction


@dataclass(frozen=True)
class ConsensusResult:
    """Resultado del proceso de consenso."""
    direction:          Direction
    agreement_ratio:    float            # M/N
    avg_confidence:     float
    composite_score:    float            # agreement * confidence
    participating:      Tuple[str, ...]
    agreeing:           Tuple[str, ...]
    signals:            Tuple[Signal, ...]
    is_actionable:      bool

class SignalConsensus:
    """
    Agrega señales de múltiples estrategias y retorna el consenso.
    """

    def __init__(
        self,
        strategies: Optional[List[BaseStrategy]] = None,
        min_agreement: float = 0.66,
        min_score: float = 0.60,
    ) -> None:
        self.strategies = strategies or []
        if strategies is not None and 0 < len(self.strategies) < 2:
             raise ValueError("SignalConsensus requires at least 2 strategies")
        self.min_agreement = min_agreement
        self.min_score = min_score
        self._logger = logging.getLogger(__name__)


    def evaluate(self, candles: NDArray[np.float64]) -> ConsensusResult:
        signals: List[Signal] = []
        participating: List[str] = []
        
        for strat in self.strategies:
            try:
                sig = strat.analyze(candles)
                signals.append(sig)
                participating.append(strat.name)
            except Exception as e:
                self._logger.warning(f"Strategy {strat.name} failed: {e}")
        
        if not signals:
            return self._empty_result()

        # Count votes
        calls = [s for s in signals if s.direction == Direction.CALL]
        puts = [s for s in signals if s.direction == Direction.PUT]
        
        num_participating = len(signals)
        num_calls = len(calls)
        num_puts = len(puts)
        
        # Determine winning direction
        if num_calls > num_puts:
            winner_direction = Direction.CALL
            agreeing_signals = calls
            agreement_ratio = num_calls / num_participating
        elif num_puts > num_calls:
            winner_direction = Direction.PUT
            agreeing_signals = puts
            agreement_ratio = num_puts / num_participating
        else:
            return self._empty_result(participating, tuple(signals))

        avg_conf = sum(s.confidence for s in agreeing_signals) / len(agreeing_signals)
        composite_score = agreement_ratio * avg_conf
        
        is_actionable = (
            agreement_ratio >= self.min_agreement and
            composite_score >= self.min_score
        )

        return ConsensusResult(
            direction=winner_direction,
            agreement_ratio=round(agreement_ratio, 2),
            avg_confidence=round(avg_conf, 2),
            composite_score=round(composite_score, 2),
            participating=tuple(participating),
            agreeing=tuple(s.strategy_id for s in agreeing_signals),
            signals=tuple(signals),
            is_actionable=is_actionable
        )

    def _empty_result(
        self, 
        participating: List[str] = None, 
        signals: Tuple[Signal, ...] = None
    ) -> ConsensusResult:
        return ConsensusResult(
            direction=Direction.HOLD,
            agreement_ratio=0.0,
            avg_confidence=0.0,
            composite_score=0.0,
            participating=tuple(participating or []),
            agreeing=(),
            signals=signals or (),
            is_actionable=False
        )

    def add_strategy(self, strategy: BaseStrategy) -> None:
        self.strategies.append(strategy)

    def remove_strategy(self, strategy_name: str) -> None:
        self.strategies = [s for s in self.strategies if s.name != strategy_name]
