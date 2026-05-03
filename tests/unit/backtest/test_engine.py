"""
tests/unit/backtest/test_engine.py
──────────────────────────────────
Pruebas unitarias del BacktestEngine scaffold (S7-T1).
"""
from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

from iqoptionapi.backtest.engine import (
    BacktestEngine,
    BacktestRun,
    BacktestTrade,
    COL_CLOSE,
    COL_TIME,
)
from iqoptionapi.strategy.base import BaseStrategy
from iqoptionapi.strategy.signal import AssetType, Direction, Signal


# ── Mock strategy configurable ───────────────────────────────────

class MockStrategy(BaseStrategy):
    """Estrategia mock cuya dirección y confianza son configurables."""

    def __init__(
        self,
        direction: Direction = Direction.CALL,
        confidence: float = 0.9,
    ) -> None:
        super().__init__(
            asset="EURUSD",
            asset_type=AssetType.BINARY,
            duration=60,
            amount=1.0,
        )
        self._direction = direction
        self._confidence = confidence

    def analyze(self, candles: NDArray[np.float64]) -> Signal:
        return self._signal(self._direction, self._confidence)


# ── Helpers ──────────────────────────────────────────────────────

def _make_candles(n: int = 50, *, uptrend: bool = True) -> NDArray[np.float64]:
    """Genera *n* velas sintéticas de 6 columnas."""
    candles = np.zeros((n, 6), dtype=np.float64)
    candles[:, COL_TIME] = np.arange(n) * 60
    if uptrend:
        candles[:, COL_CLOSE] = np.linspace(100, 110, n)
    else:
        candles[:, COL_CLOSE] = np.linspace(110, 100, n)
    # open = close shifted (simplificado)
    candles[:, 1] = candles[:, COL_CLOSE] - 0.1
    candles[:, 2] = candles[:, COL_CLOSE] + 0.5  # high
    candles[:, 3] = candles[:, COL_CLOSE] - 0.5  # low
    candles[:, 5] = 1000  # volume
    return candles


# ════════════════════════════════════════════════════════════════
# 1. Validaciones del constructor
# ════════════════════════════════════════════════════════════════

def test_engine_raises_on_bad_candle_shape():
    """candles.shape[1] != 6 → ValueError."""
    strategy = MockStrategy()
    bad_candles = np.zeros((50, 5))
    with pytest.raises(ValueError, match="shape \\(N, 6\\)"):
        BacktestEngine(strategy, bad_candles)


def test_engine_raises_on_insufficient_candles():
    """len(candles) < min_candles → ValueError."""
    strategy = MockStrategy()
    candles = np.zeros((10, 6))
    with pytest.raises(ValueError, match="Need at least 30 candles"):
        BacktestEngine(strategy, candles, min_candles=30)


def test_engine_raises_on_bad_balance():
    """initial_balance <= 0 → ValueError."""
    strategy = MockStrategy()
    candles = _make_candles(50)
    with pytest.raises(ValueError, match="initial_balance must be > 0"):
        BacktestEngine(strategy, candles, initial_balance=0)
    with pytest.raises(ValueError, match="initial_balance must be > 0"):
        BacktestEngine(strategy, candles, initial_balance=-100)


# ════════════════════════════════════════════════════════════════
# 2. Ejecución del backtest
# ════════════════════════════════════════════════════════════════

def test_run_returns_backtest_run():
    """run() retorna un BacktestRun con trades cuando la estrategia da CALL."""
    strategy = MockStrategy(direction=Direction.CALL)
    candles = _make_candles(50, uptrend=True)
    engine = BacktestEngine(
        strategy, candles, initial_balance=1000, trade_amount=10, min_candles=30
    )
    result = engine.run()

    assert isinstance(result, BacktestRun)
    assert result.strategy_name == "MockStrategy"
    assert result.initial_balance == 1000.0
    assert result.total_trades > 0
    assert all(isinstance(t, BacktestTrade) for t in result.trades)


def test_run_hold_signals_are_skipped():
    """Strategy que retorna HOLD → 0 trades."""
    strategy = MockStrategy(direction=Direction.HOLD)
    candles = _make_candles(50, uptrend=True)
    engine = BacktestEngine(
        strategy, candles, initial_balance=1000, trade_amount=10, min_candles=30
    )
    result = engine.run()

    assert result.total_trades == 0
    assert result.final_balance == 1000.0


def test_run_win_increases_balance():
    """CALL en tendencia alcista → WIN, balance sube."""
    strategy = MockStrategy(direction=Direction.CALL)
    candles = _make_candles(50, uptrend=True)
    engine = BacktestEngine(
        strategy,
        candles,
        initial_balance=1000,
        trade_amount=10,
        payout=0.82,
        min_candles=30,
    )
    result = engine.run()

    first_trade = result.trades[0]
    assert first_trade.result == "WIN"
    expected_balance = 1000 + 10 * 0.82
    assert first_trade.balance_after == pytest.approx(expected_balance)


def test_run_loss_decreases_balance():
    """CALL en tendencia bajista → LOSS, balance baja."""
    strategy = MockStrategy(direction=Direction.CALL)
    candles = _make_candles(50, uptrend=False)
    engine = BacktestEngine(
        strategy,
        candles,
        initial_balance=1000,
        trade_amount=10,
        payout=0.82,
        min_candles=30,
    )
    result = engine.run()

    first_trade = result.trades[0]
    assert first_trade.result == "LOSS"
    expected_balance = 1000 - 10
    assert first_trade.balance_after == pytest.approx(expected_balance)


def test_run_stops_on_ruin():
    """balance <= 0 → backtest se detiene antes de agotar todas las velas."""
    strategy = MockStrategy(direction=Direction.CALL)
    # Tendencia bajista + balance justo para 1 loss
    candles = _make_candles(50, uptrend=False)
    engine = BacktestEngine(
        strategy,
        candles,
        initial_balance=10,
        trade_amount=10,
        payout=0.82,
        min_candles=30,
    )
    result = engine.run()

    assert result.final_balance <= 0
    # No puede tener más trades de los que el balance permite
    # Con balance=10 y trade_amount=10, el primer LOSS lleva a 0
    assert result.total_trades == 1
    assert result.trades[-1].balance_after <= 0


# ════════════════════════════════════════════════════════════════
# 3. Propiedades calculadas
# ════════════════════════════════════════════════════════════════

def test_win_rate_calculation():
    """3 WIN + 1 LOSS → win_rate == 0.75."""
    run = BacktestRun(
        strategy_name="test",
        initial_balance=1000,
        final_balance=1000,
        trades=[
            BacktestTrade(
                candle_index=i,
                entry_time=float(i * 60),
                entry_price=100.0,
                exit_price=101.0,
                direction=Direction.CALL,
                signal_confidence=0.9,
                result="WIN" if i < 3 else "LOSS",
                profit=8.2 if i < 3 else -10.0,
                balance_after=1000.0,
            )
            for i in range(4)
        ],
        candles_total=50,
        candles_analyzed=4,
    )
    assert run.win_rate == pytest.approx(0.75)
    assert run.winning_trades == 3
    assert run.total_trades == 4


def test_total_profit_calculation():
    """Suma de profits individuales == total_profit."""
    trades = [
        BacktestTrade(
            candle_index=i,
            entry_time=float(i * 60),
            entry_price=100.0,
            exit_price=101.0,
            direction=Direction.CALL,
            signal_confidence=0.9,
            result="WIN",
            profit=8.2,
            balance_after=1000.0 + 8.2 * (i + 1),
        )
        for i in range(3)
    ] + [
        BacktestTrade(
            candle_index=3,
            entry_time=180.0,
            entry_price=100.0,
            exit_price=99.0,
            direction=Direction.CALL,
            signal_confidence=0.9,
            result="LOSS",
            profit=-10.0,
            balance_after=1000.0 + 8.2 * 3 - 10.0,
        )
    ]

    run = BacktestRun(
        strategy_name="test",
        initial_balance=1000,
        final_balance=1000 + sum(t.profit for t in trades),
        trades=trades,
        candles_total=50,
        candles_analyzed=4,
    )

    expected_total = 8.2 * 3 + (-10.0)
    assert run.total_profit == pytest.approx(expected_total)
    assert run.total_profit == pytest.approx(sum(t.profit for t in run.trades))
