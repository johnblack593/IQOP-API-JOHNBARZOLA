"""
tests/unit/backtest/test_backtest_metrics.py
────────────────────────────────────────────
Pruebas unitarias de métricas avanzadas de BacktestRun (S7-T2).
"""
from __future__ import annotations

import math

import pytest

from iqoptionapi.backtest.engine import BacktestRun, BacktestTrade
from iqoptionapi.strategy.signal import Direction


# ── Helper ───────────────────────────────────────────────────────

def make_run(
    trades_data: list[tuple[str, float, float]],
    initial_balance: float = 1000.0,
) -> BacktestRun:
    """
    Genera un BacktestRun con trades controlados.

    Args:
        trades_data: lista de ``(result, profit, balance_after)``
        initial_balance: saldo inicial del run
    """
    trades = [
        BacktestTrade(
            candle_index=i,
            entry_time=float(i * 60),
            entry_price=100.0,
            exit_price=101.0 if r == "WIN" else 99.0,
            direction=Direction.CALL,
            signal_confidence=0.8,
            result=r,
            profit=p,
            balance_after=b,
        )
        for i, (r, p, b) in enumerate(trades_data)
    ]
    final_bal = trades[-1].balance_after if trades else initial_balance
    return BacktestRun(
        strategy_name="test",
        initial_balance=initial_balance,
        final_balance=final_bal,
        trades=trades,
        candles_total=100,
        candles_analyzed=len(trades),
    )


# ════════════════════════════════════════════════════════════════
# Sharpe Ratio
# ════════════════════════════════════════════════════════════════

def test_sharpe_ratio_positive_for_net_win():
    """Mix de profits con neto positivo → sharpe > 0."""
    run = make_run([
        ("WIN",  8.2, 1008.2),
        ("WIN",  8.2, 1016.4),
        ("LOSS", -10.0, 1006.4),
        ("WIN",  8.2, 1014.6),
    ])
    assert run.sharpe_ratio > 0


def test_sharpe_ratio_zero_on_empty_trades():
    """Sin trades → sharpe_ratio == 0.0."""
    run = BacktestRun(
        strategy_name="test",
        initial_balance=1000.0,
        final_balance=1000.0,
        trades=[],
        candles_total=100,
        candles_analyzed=0,
    )
    assert run.sharpe_ratio == 0.0


def test_sharpe_ratio_zero_when_std_is_zero():
    """Profits idénticos → std=0 → sharpe == 0.0."""
    run = make_run([
        ("WIN", 8.2, 1008.2),
        ("WIN", 8.2, 1016.4),
        ("WIN", 8.2, 1024.6),
    ])
    assert run.sharpe_ratio == 0.0


# ════════════════════════════════════════════════════════════════
# Max Drawdown
# ════════════════════════════════════════════════════════════════

def test_max_drawdown_no_trades():
    """Sin trades → max_drawdown == 0.0."""
    run = BacktestRun(
        strategy_name="test",
        initial_balance=1000.0,
        final_balance=1000.0,
        trades=[],
        candles_total=100,
        candles_analyzed=0,
    )
    assert run.max_drawdown == 0.0


def test_max_drawdown_calculated_correctly():
    """
    Balance path: 1000 → 1100 → 1050 → 1000
    Peak = 1100, trough = 1000 → drawdown = 100.
    """
    run = make_run([
        ("WIN",  100.0, 1100.0),
        ("LOSS", -50.0, 1050.0),
        ("LOSS", -50.0, 1000.0),
    ])
    assert run.max_drawdown == pytest.approx(100.0)


def test_max_drawdown_pct_calculation():
    """max_drawdown_pct = 100 / 1100 * 100 ≈ 9.0909%."""
    run = make_run([
        ("WIN",  100.0, 1100.0),
        ("LOSS", -50.0, 1050.0),
        ("LOSS", -50.0, 1000.0),
    ])
    expected_pct = 100.0 / 1100.0 * 100
    assert run.max_drawdown_pct == pytest.approx(expected_pct, rel=1e-4)


# ════════════════════════════════════════════════════════════════
# Profit Factor
# ════════════════════════════════════════════════════════════════

def test_profit_factor_normal_case():
    """gross_profit=246, gross_loss=20 → PF = 12.3."""
    run = make_run([
        ("WIN",   82.0, 1082.0),
        ("WIN",   82.0, 1164.0),
        ("WIN",   82.0, 1246.0),
        ("LOSS", -10.0, 1236.0),
        ("LOSS", -10.0, 1226.0),
    ])
    assert run.profit_factor == pytest.approx(246.0 / 20.0, rel=1e-4)


def test_profit_factor_zero_loss():
    """Solo wins → profit_factor == inf."""
    run = make_run([
        ("WIN", 8.2, 1008.2),
        ("WIN", 8.2, 1016.4),
    ])
    assert math.isinf(run.profit_factor)
    assert run.profit_factor > 0


def test_profit_factor_no_trades():
    """Sin trades → profit_factor == 0.0."""
    run = BacktestRun(
        strategy_name="test",
        initial_balance=1000.0,
        final_balance=1000.0,
        trades=[],
        candles_total=100,
        candles_analyzed=0,
    )
    assert run.profit_factor == 0.0


# ════════════════════════════════════════════════════════════════
# Expectancy
# ════════════════════════════════════════════════════════════════

def test_expectancy_positive():
    """75% win_rate, avg_win=8.2, avg_loss=-10 → 3.65."""
    run = make_run([
        ("WIN",   8.2, 1008.2),
        ("WIN",   8.2, 1016.4),
        ("WIN",   8.2, 1024.6),
        ("LOSS", -10.0, 1014.6),
    ])
    expected = 0.75 * 8.2 + 0.25 * (-10.0)  # 3.65
    assert run.expectancy == pytest.approx(expected, rel=1e-4)


def test_expectancy_zero_trades():
    """Sin trades → expectancy == 0.0."""
    run = BacktestRun(
        strategy_name="test",
        initial_balance=1000.0,
        final_balance=1000.0,
        trades=[],
        candles_total=100,
        candles_analyzed=0,
    )
    assert run.expectancy == 0.0


# ════════════════════════════════════════════════════════════════
# Consecutive Streaks
# ════════════════════════════════════════════════════════════════

def test_max_consecutive_wins():
    """WIN, WIN, WIN, LOSS, WIN → max_consecutive_wins == 3."""
    run = make_run([
        ("WIN",   8.2, 1008.2),
        ("WIN",   8.2, 1016.4),
        ("WIN",   8.2, 1024.6),
        ("LOSS", -10.0, 1014.6),
        ("WIN",   8.2, 1022.8),
    ])
    assert run.max_consecutive_wins == 3


def test_max_consecutive_losses():
    """WIN, LOSS, LOSS, LOSS, WIN, LOSS → max_consecutive_losses == 3."""
    run = make_run([
        ("WIN",    8.2, 1008.2),
        ("LOSS", -10.0,  998.2),
        ("LOSS", -10.0,  988.2),
        ("LOSS", -10.0,  978.2),
        ("WIN",    8.2,  986.4),
        ("LOSS", -10.0,  976.4),
    ])
    assert run.max_consecutive_losses == 3


# ════════════════════════════════════════════════════════════════
# Safety: single trade
# ════════════════════════════════════════════════════════════════

def test_all_metrics_no_exception_on_single_trade():
    """1 trade → all properties return without raising."""
    run = make_run([("WIN", 8.2, 1008.2)])

    # Access every metric — none should raise
    assert isinstance(run.sharpe_ratio, float)
    assert isinstance(run.max_drawdown, float)
    assert isinstance(run.max_drawdown_pct, float)
    assert isinstance(run.profit_factor, float)
    assert isinstance(run.expectancy, float)
    assert isinstance(run.max_consecutive_wins, int)
    assert isinstance(run.max_consecutive_losses, int)
    assert isinstance(run.win_rate, float)
    assert isinstance(run.total_profit, float)
