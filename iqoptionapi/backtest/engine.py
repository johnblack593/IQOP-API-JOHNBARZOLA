"""
iqoptionapi/backtest/engine.py
──────────────────────────────
BacktestEngine — reproduce señales históricas sobre un dataset de
velas numpy y mide el P&L simulado sin conexión al servidor real.

Sprint 7 · Tarea S7-T1
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np
from numpy.typing import NDArray

from iqoptionapi.strategy.base import BaseStrategy
from iqoptionapi.strategy.signal import Direction

# ── Índices de columnas del array de velas (N, 6) ────────────────
COL_TIME: int = 0
COL_OPEN: int = 1
COL_HIGH: int = 2
COL_LOW: int = 3
COL_CLOSE: int = 4
COL_VOL: int = 5


# ── Resultado de un trade individual ─────────────────────────────
@dataclass(frozen=True)
class BacktestTrade:
    """Registro inmutable de un trade ejecutado durante el backtest."""

    candle_index: int
    entry_time: float
    entry_price: float
    exit_price: float
    direction: Direction
    signal_confidence: float
    result: str  # "WIN" | "LOSS"
    profit: float
    balance_after: float


# ── Resultado agregado de una corrida completa ───────────────────
@dataclass
class BacktestRun:
    """Resultado agregado de una corrida de backtest."""

    strategy_name: str
    initial_balance: float
    final_balance: float
    trades: List[BacktestTrade] = field(default_factory=list)
    candles_total: int = 0
    candles_analyzed: int = 0

    # -- propiedades calculadas -----------------------------------------

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def winning_trades(self) -> int:
        return sum(1 for t in self.trades if t.result == "WIN")

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        return self.winning_trades / self.total_trades

    @property
    def total_profit(self) -> float:
        return sum(t.profit for t in self.trades)


# ── Motor de backtesting ─────────────────────────────────────────
class BacktestEngine:
    """
    Motor de backtest que reproduce velas históricas en orden
    cronológico, invoca ``strategy.analyze()`` en cada ventana
    deslizante y registra las señales y P&L resultantes.

    Args:
        strategy:        Estrategia que implementa ``BaseStrategy``.
        candles:         Array numpy de forma ``(N, 6)`` con columnas
                         ``[time, open, high, low, close, vol]``.
        initial_balance: Saldo inicial en USD.
        trade_amount:    Monto fijo por operación.
        payout:          Porcentaje de payout (0 < payout ≤ 1).
        min_candles:     Mínimo de velas necesarias antes de generar
                         la primera señal.
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        candles: NDArray[np.float64],
        initial_balance: float = 1000.0,
        trade_amount: float = 10.0,
        payout: float = 0.82,
        min_candles: int = 30,
    ) -> None:
        # ── Validaciones ──────────────────────────────────────────
        if candles.ndim != 2 or candles.shape[1] != 6:
            raise ValueError(
                "candles must have shape (N, 6): time,open,high,low,close,vol"
            )
        if len(candles) < min_candles:
            raise ValueError(
                f"Need at least {min_candles} candles, got {len(candles)}"
            )
        if initial_balance <= 0:
            raise ValueError(
                f"initial_balance must be > 0, got {initial_balance}"
            )
        if trade_amount <= 0:
            raise ValueError(
                f"trade_amount must be > 0, got {trade_amount}"
            )
        if payout <= 0 or payout > 1:
            raise ValueError(
                f"payout must be in (0, 1], got {payout}"
            )

        self._strategy = strategy
        self._candles = candles
        self._initial_balance = initial_balance
        self._trade_amount = trade_amount
        self._payout = payout
        self._min_candles = min_candles

    # ── Replay principal ──────────────────────────────────────────

    def run(self) -> BacktestRun:
        """
        Ejecuta el replay cronológico completo.

        Para cada posición ``i`` desde ``min_candles`` hasta
        ``len(candles) - 1``:

        1. Extrae la ventana ``candles[i - min_candles : i]``.
        2. Invoca ``strategy.analyze(window)`` → ``Signal``.
        3. Si la señal es HOLD, la ignora.
        4. Si es CALL/PUT, toma ``entry = candles[i]`` y
           ``exit = candles[i+1]`` y calcula el resultado.
        5. Actualiza balance; detiene si llega a ruina (≤ 0).

        Returns:
            ``BacktestRun`` con los trades registrados.
        """
        candles = self._candles
        balance = self._initial_balance
        trades: list[BacktestTrade] = []
        candles_analyzed = 0

        # i recorre desde min_candles hasta len-1 (necesitamos i+1 para salida)
        last_index = len(candles) - 1
        for i in range(self._min_candles, last_index):
            # 1. Ventana deslizante
            window = candles[i - self._min_candles : i]

            # 2. Evaluar estrategia
            signal = self._strategy.analyze(window)
            candles_analyzed += 1

            # 3. Si HOLD → skip
            if signal.direction == Direction.HOLD:
                continue

            # 4. Calcular trade
            entry_price = float(candles[i][COL_CLOSE])
            exit_price = float(candles[i + 1][COL_CLOSE])

            if signal.direction == Direction.CALL:
                win = exit_price > entry_price
            else:  # PUT
                win = exit_price < entry_price

            if win:
                profit = self._trade_amount * self._payout
                result = "WIN"
            else:
                profit = -self._trade_amount
                result = "LOSS"

            balance += profit

            trade = BacktestTrade(
                candle_index=i,
                entry_time=float(candles[i][COL_TIME]),
                entry_price=entry_price,
                exit_price=exit_price,
                direction=signal.direction,
                signal_confidence=signal.confidence,
                result=result,
                profit=profit,
                balance_after=balance,
            )
            trades.append(trade)

            # 5. Detener si ruina
            if balance <= 0:
                break

        return BacktestRun(
            strategy_name=self._strategy.name,
            initial_balance=self._initial_balance,
            final_balance=balance,
            trades=trades,
            candles_total=len(candles),
            candles_analyzed=candles_analyzed,
        )
