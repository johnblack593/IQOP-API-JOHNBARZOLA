"""
iqoptionapi/signal_consensus.py
───────────────────────────────
Combinador de señales de múltiples estrategias (Consenso M-de-N).
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional
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

    Uso con señales del servidor:
    result = consensus.evaluate_with_server(candles, server_indicators)
    """

    def __init__(
        self,
        strategies: Optional[List[BaseStrategy]] = None,
        min_agreement: float = 0.66,
        min_score: float = 0.60,
        server_signal_boost: float = 0.10,
    ) -> None:
        self.strategies = strategies or []
        if strategies is not None and 0 < len(self.strategies) < 2:
             raise ValueError("SignalConsensus requires at least 2 strategies")
        self.min_agreement = min_agreement
        self.min_score = min_score
        self.server_signal_boost = server_signal_boost
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

    def _parse_server_direction(
        self, server_indicators: dict
    ) -> Direction:
        """
        Interpreta el dict de indicadores del servidor IQ Option y
        retorna la dirección dominante (CALL, PUT o HOLD).

        El servidor retorna un dict con claves como 'ma', 'ema', 'rsi',
        'macd', 'stochastic', 'bollinger' donde cada valor tiene
        {'signal': 'BUY'|'SELL'|'NEUTRAL', ...}.

        Voting: cuenta BUY vs SELL entre todos los indicadores presentes.
        """
        if not server_indicators:
            return Direction.HOLD
        buy_votes = 0
        sell_votes = 0
        for key, data in server_indicators.items():
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

    def evaluate_with_server(
        self,
        candles: NDArray[np.float64],
        server_indicators: dict | None = None,
    ) -> ConsensusResult:
        """
        Evalúa el consenso local y aplica un boost al composite_score
        si las señales del servidor confirman la misma dirección.

        Args:
            candles:           Array numpy de velas para las estrategias locales.
            server_indicators: Dict de indicadores del servidor IQ Option,
                               tal como retorna get_technical_indicators().
                               Si es None, equivale a llamar evaluate() directamente.

        Returns:
            ConsensusResult con composite_score potencialmente boosteado.
            El campo `signals` incluye metadata indicando si el servidor confirmó.
        """
        result = self.evaluate(candles)

        if not server_indicators or result.direction == Direction.HOLD:
            return result

        server_dir = self._parse_server_direction(server_indicators)
        server_confirmed = (server_dir == result.direction)

        if server_confirmed:
            boosted_score = min(1.0, result.composite_score + self.server_signal_boost)
            boosted_actionable = (
                result.agreement_ratio >= self.min_agreement
                and boosted_score >= self.min_score
            )
            self._logger.debug(
                "Server confirmed %s: composite_score %.2f → %.2f",
                result.direction, result.composite_score, boosted_score
            )
            # Reconstruir ConsensusResult con score boosteado
            # (frozen dataclass → crear nuevo)
            result = ConsensusResult(
                direction=result.direction,
                agreement_ratio=result.agreement_ratio,
                avg_confidence=result.avg_confidence,
                composite_score=round(boosted_score, 2),
                participating=result.participating,
                agreeing=result.agreeing,
                signals=result.signals,
                is_actionable=boosted_actionable,
            )
        else:
            self._logger.debug(
                "Server direction %s conflicts with local %s — no boost applied",
                server_dir, result.direction
            )

        return result

    def add_strategy(self, strategy: BaseStrategy) -> None:
        self.strategies.append(strategy)

    def remove_strategy(self, strategy_name: str) -> None:
        self.strategies = [s for s in self.strategies if s.name != strategy_name]
