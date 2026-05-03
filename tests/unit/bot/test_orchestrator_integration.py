"""
tests/unit/bot/test_orchestrator_integration.py
────────────────────────────────────────────────
Pruebas de integración del BotOrchestrator con CircuitBreaker y TradeJournal.
"""
from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from iqoptionapi.bot.orchestrator import BotOrchestrator
from iqoptionapi.strategy.signal import Direction
from iqoptionapi.strategy.signal_consensus import ConsensusResult


@pytest.fixture
def mock_iq():
    iq = MagicMock()
    iq.get_candles.return_value = [
        {"from": i, "open": 1.1, "max": 1.2, "min": 1.0, "close": 1.1, "volume": 100}
        for i in range(50)
    ]
    iq.buy.return_value = (True, 123456)
    iq.get_balance.return_value = 1000.0
    iq.check_win_v3.return_value = (True, 1.85)
    return iq


@pytest.fixture
def mock_consensus():
    consensus = MagicMock()
    consensus.evaluate.return_value = ConsensusResult(
        direction=Direction.CALL,
        agreement_ratio=1.0,
        avg_confidence=1.0,
        composite_score=1.0,
        participating=("S1",),
        agreeing=("S1",),
        signals=(),
        is_actionable=True
    )
    return consensus


@pytest.fixture
def mock_cb():
    cb = MagicMock()
    cb.is_open.return_value = False
    cb.status_report.return_value = {"state": "closed"}
    return cb


@pytest.fixture
def mock_journal():
    journal = MagicMock()
    journal.get_trades_today.return_value = []
    return journal


# ════════════════════════════════════════════════════════════════
# Pruebas de CircuitBreaker
# ════════════════════════════════════════════════════════════════

def test_circuit_breaker_open_skips_tick(mock_iq, mock_consensus, mock_cb):
    """Si el CB está abierto, el tick debe abortar antes de evaluar."""
    mock_cb.is_open.return_value = True
    bot = BotOrchestrator(mock_iq, mock_consensus, circuit_breaker=mock_cb)
    
    bot._tick()
    
    mock_cb.is_open.assert_called_once()
    mock_consensus.evaluate.assert_not_called()


def test_circuit_breaker_closed_allows_tick(mock_iq, mock_consensus, mock_cb):
    """Si el CB está cerrado, el tick debe evaluar normalmente."""
    mock_cb.is_open.return_value = False
    bot = BotOrchestrator(mock_iq, mock_consensus, circuit_breaker=mock_cb)
    
    bot._tick()
    
    mock_cb.is_open.assert_called_once()
    mock_consensus.evaluate.assert_called_once()


def test_no_circuit_breaker_runs_normally(mock_iq, mock_consensus):
    """Si no hay CB, el orquestador funciona normalmente."""
    bot = BotOrchestrator(mock_iq, mock_consensus, circuit_breaker=None)
    bot._tick()
    mock_consensus.evaluate.assert_called_once()


def test_balance_update_called_after_tick(mock_iq, mock_consensus, mock_cb):
    """Verificar que se actualiza el balance en el CB después de un tick (no dry_run)."""
    bot = BotOrchestrator(mock_iq, mock_consensus, circuit_breaker=mock_cb, dry_run=False)
    bot._tick()
    
    mock_iq.get_balance.assert_called_once()
    mock_cb._update_balance_metrics.assert_called_with(1000.0)


def test_balance_update_not_called_without_cb(mock_iq, mock_consensus):
    """Si no hay CB, no se debe llamar a get_balance()."""
    bot = BotOrchestrator(mock_iq, mock_consensus, circuit_breaker=None, dry_run=False)
    bot._tick()
    mock_iq.get_balance.assert_not_called()


# ════════════════════════════════════════════════════════════════
# Pruebas de TradeJournal
# ════════════════════════════════════════════════════════════════

def test_journal_passed_to_orchestrator(mock_iq, mock_consensus, mock_journal):
    """Verificar que el journal se guarda correctamente en el init."""
    bot = BotOrchestrator(mock_iq, mock_consensus, journal=mock_journal)
    assert bot.journal == mock_journal


def test_status_includes_circuit_breaker_report(mock_iq, mock_consensus, mock_cb):
    """El status debe incluir el reporte del CB."""
    bot = BotOrchestrator(mock_iq, mock_consensus, circuit_breaker=mock_cb)
    status = bot.status()
    assert status["circuit_breaker"] == {"state": "closed"}


def test_status_circuit_breaker_none_without_cb(mock_iq, mock_consensus):
    """El status debe tener CB como None si no se provee."""
    bot = BotOrchestrator(mock_iq, mock_consensus, circuit_breaker=None)
    status = bot.status()
    assert status["circuit_breaker"] is None


def test_execute_order_calls_journal_record_async(mock_iq, mock_consensus, mock_journal):
    """Verificar que se dispare el registro asíncrono en el journal."""
    bot = BotOrchestrator(mock_iq, mock_consensus, journal=mock_journal, dry_run=False)
    
    # Patching _record_trade_async to verify it was called
    with patch.object(bot, '_record_trade_async') as mock_record:
        bot._tick()
        mock_record.assert_called_once_with(123456, "call", 1.0)


def test_execute_order_no_journal_no_crash(mock_iq, mock_consensus):
    """Verificar que no falle si no hay journal."""
    bot = BotOrchestrator(mock_iq, mock_consensus, journal=None, dry_run=False)
    # No debe lanzar excepción
    bot._tick()
    assert bot._trade_count == 1
