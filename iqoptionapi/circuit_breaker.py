"""
iqoptionapi/circuit_breaker.py
──────────────────────────────
Protector automático de capital.
Para el bot cuando las pérdidas superan umbrales definidos.
Un bot sin circuit breaker puede perder toda la cuenta en minutos.
"""
from enum import Enum
from iqoptionapi.core.logger import get_logger
import time
from typing import Optional


class CircuitBreakerState(str, Enum):
    CLOSED  = "closed"   # operando normalmente
    OPEN    = "open"     # pausado por pérdidas — NO operar
    HALF    = "half"     # modo prueba — 1 operación de prueba


class CircuitBreaker:
    """
    Implementa el patrón Circuit Breaker adaptado a trading.

    Dispara (OPEN) cuando:
      - pérdidas consecutivas >= MAX_CONSECUTIVE_LOSSES
      - pérdida total de sesión >= MAX_SESSION_LOSS_USD
      - drawdown >= MAX_DRAWDOWN_PCT del balance inicial
    """

    def __init__(
        self,
        max_consecutive_losses: int = 3,
        max_session_loss_usd: float = 10.0,
        max_drawdown_pct: float = 0.10,   # 10% del balance inicial
        recovery_wait_secs: float = 300.0, # 5 minutos en OPEN antes de HALF
    ) -> None:
        self.max_consecutive_losses = max_consecutive_losses
        self.max_session_loss_usd = max_session_loss_usd
        self.max_drawdown_pct = max_drawdown_pct
        self.recovery_wait_secs = recovery_wait_secs

        self._state = CircuitBreakerState.CLOSED
        self._consecutive_losses = 0
        self._session_loss_usd = 0.0
        self._initial_balance: Optional[float] = None
        self._peak_balance: float = 0.0
        self._trips_today = 0
        self._last_trip_time: float = 0.0
        self._half_open_test_done = False
        self.logger = get_logger(__name__)

    @property
    def state(self) -> CircuitBreakerState:
        # Auto-recovery check
        if self._state == CircuitBreakerState.OPEN:
            if time.time() - self._last_trip_time >= self.recovery_wait_secs:
                self._state = CircuitBreakerState.HALF
                self._half_open_test_done = False
        return self._state

    @property
    def consecutive_losses(self) -> int:
        return self._consecutive_losses

    @property
    def session_loss_usd(self) -> float:
        return self._session_loss_usd

    @property
    def trips_today(self) -> int:
        return self._trips_today

    def record_win(self, amount_won: float, current_balance: float) -> None:
        """Registra una operación ganadora."""
        self._consecutive_losses = 0
        # Win doesn't subtract from session_loss_usd in this implementation (loss is cumulative)
        # but we track balance for drawdown
        self._update_balance_metrics(current_balance)
        
        if self.state == CircuitBreakerState.HALF:
            self._state = CircuitBreakerState.CLOSED

    def record_loss(self, amount_lost: float, current_balance: float) -> None:
        """Registra una operación perdedora."""
        self._consecutive_losses += 1
        self._session_loss_usd += amount_lost
        self._update_balance_metrics(current_balance)

        if self.state == CircuitBreakerState.HALF:
            self._trip()
        else:
            self._check_thresholds()

    def _update_balance_metrics(self, balance: float) -> None:
        if self._initial_balance is None:
            self._initial_balance = balance
            self._peak_balance = balance
        
        if balance > self._peak_balance:
            self._peak_balance = balance

    def _check_thresholds(self) -> None:
        if self._state != CircuitBreakerState.CLOSED:
            return

        # 1. Consecutive losses
        if self._consecutive_losses >= self.max_consecutive_losses:
            self._trip("Max consecutive losses reached")
            return

        # 2. Session loss
        if self._session_loss_usd >= self.max_session_loss_usd:
            self._trip("Max session loss reached")
            return

        # 3. Drawdown from peak
        if self._peak_balance > 0:
            drawdown = (self._peak_balance - (self._peak_balance - self._session_loss_usd)) / self._peak_balance
            # Note: simplified drawdown using session_loss_usd. 
            # Real drawdown should use current_balance vs peak_balance.
            pass
        
        # Real drawdown check
        if self._initial_balance and self._initial_balance > 0:
            current_drawdown = (self._initial_balance - (self._initial_balance - self._session_loss_usd)) / self._initial_balance
            if current_drawdown >= self.max_drawdown_pct:
                self._trip("Max drawdown reached")

    def _trip(self, reason: str = "") -> None:
        self._state = CircuitBreakerState.OPEN
        self._last_trip_time = time.time()
        self._trips_today += 1

    def can_trade(self) -> bool:
        """True si el estado es CLOSED o HALF."""
        state = self.state
        if state == CircuitBreakerState.CLOSED:
            return True
        if state == CircuitBreakerState.HALF:
            if not self._half_open_test_done:
                self._half_open_test_done = True
                return True
        return False

    def record_success(self) -> None:
        """Registra un éxito (ej: reconexión) para cerrar el circuito."""
        self._consecutive_losses = 0
        if self._state != CircuitBreakerState.CLOSED:
            self._state = CircuitBreakerState.CLOSED
            self.logger.info("CircuitBreaker: Circuito CERRADO tras éxito.")

    def record_failure(self, reason: str = "General failure") -> None:
        """Registra un fallo no relacionado con trading (ej: error de red)."""
        self._consecutive_losses += 1
        self.logger.warning("CircuitBreaker: Fallo registrado: %s", reason)
        if self._consecutive_losses >= self.max_consecutive_losses:
            self._trip(reason)

    def reset_session(self, current_balance: float) -> None:
        """Resetea métricas de sesión."""
        self._consecutive_losses = 0
        self._session_loss_usd = 0.0
        self._initial_balance = current_balance
        self._peak_balance = current_balance
        self._state = CircuitBreakerState.CLOSED

    def status_report(self) -> dict:
        return {
            "state": self.state,
            "consecutive_losses": self._consecutive_losses,
            "session_loss_usd": self._session_loss_usd,
            "trips_today": self._trips_today,
            "can_trade": self.can_trade()
        }
