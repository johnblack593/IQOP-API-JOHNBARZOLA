"""
tests/unit/bot/test_orchestrator.py
───────────────────────────────────
Pruebas unitarias del BotOrchestrator scaffold (S8-T1).
"""
from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from iqoptionapi.bot.orchestrator import BotOrchestrator
from iqoptionapi.strategy.signal import Direction
from iqoptionapi.strategy.signal_consensus import ConsensusResult


# ── Mocks compartidos ──────────────────────────────────────────

@pytest.fixture
def mock_iq():
    iq = MagicMock()
    # get_candles retorna una vela mínima para evitar errores de fetch
    iq.get_candles.return_value = [
        {"from": i, "open": 1.1, "max": 1.2, "min": 1.0, "close": 1.1, "volume": 100}
        for i in range(50)
    ]
    iq.buy.return_value = (True, 123456)
    return iq


@pytest.fixture
def mock_consensus():
    consensus = MagicMock()
    # Por defecto retorna HOLD (no accionable)
    consensus.evaluate.return_value = ConsensusResult(
        direction=Direction.HOLD,
        agreement_ratio=0.0,
        avg_confidence=0.0,
        composite_score=0.0,
        participating=(),
        agreeing=(),
        signals=(),
        is_actionable=False
    )
    return consensus


# ════════════════════════════════════════════════════════════════
# 1. Ciclo de vida y Estado
# ════════════════════════════════════════════════════════════════

def test_orchestrator_not_running_initially(mock_iq, mock_consensus):
    """is_running() == False antes de start()."""
    bot = BotOrchestrator(mock_iq, mock_consensus)
    assert bot.is_running() is False


def test_orchestrator_starts_and_stops(mock_iq, mock_consensus):
    """Verificar que start() lanza el thread y stop() lo detiene."""
    # timeframe corto para que el loop no tarde en el primer sleep si el test es lento
    bot = BotOrchestrator(mock_iq, mock_consensus, timeframe=0.01)
    
    bot.start()
    assert bot.is_running() is True
    assert "iqopt-orchestrator" in [t.name for t in threading.enumerate()]
    
    bot.stop()
    assert bot.is_running() is False


def test_orchestrator_status_dry_run(mock_iq, mock_consensus):
    """status()["dry_run"] == True por defecto."""
    bot = BotOrchestrator(mock_iq, mock_consensus)
    status = bot.status()
    assert status["dry_run"] is True
    assert status["asset"] == "EURUSD"
    assert status["trade_count"] == 0


def test_double_start_no_exception(mock_iq, mock_consensus):
    """Llamar start() dos veces → no lanza excepción, loguea warning."""
    bot = BotOrchestrator(mock_iq, mock_consensus, timeframe=0.1)
    bot.start()
    bot.start()  # No debe explotar
    assert bot.is_running() is True
    bot.stop()


def test_stop_without_start_no_exception(mock_iq, mock_consensus):
    """Llamar stop() sin haber llamado start() → no lanza excepción."""
    bot = BotOrchestrator(mock_iq, mock_consensus)
    bot.stop()  # No debe explotar


# ════════════════════════════════════════════════════════════════
# 2. Lógica de Ticks y Candles
# ════════════════════════════════════════════════════════════════

def test_fetch_candles_returns_none_on_empty(mock_iq, mock_consensus):
    """Mock de iq.get_candles() retorna [] → _fetch_candles() == None."""
    mock_iq.get_candles.return_value = []
    bot = BotOrchestrator(mock_iq, mock_consensus)
    assert bot._fetch_candles() is None


def test_fetch_candles_converts_to_numpy(mock_iq, mock_consensus):
    """Verificar conversión de lista de dicts a numpy array (N, 6)."""
    bot = BotOrchestrator(mock_iq, mock_consensus)
    arr = bot._fetch_candles()
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (50, 6)
    # [from, open, max, min, close, volume]
    assert arr[0][0] == 0.0
    assert arr[0][1] == 1.1


def test_tick_skips_on_insufficient_candles(mock_iq, mock_consensus):
    """_fetch_candles() retorna array de 5 velas → _tick() no llama evaluate."""
    mock_iq.get_candles.return_value = [
        {"from": i, "open": 1.1, "max": 1.2, "min": 1.0, "close": 1.1, "volume": 100}
        for i in range(5)
    ]
    bot = BotOrchestrator(mock_iq, mock_consensus)
    bot._tick()
    mock_consensus.evaluate.assert_not_called()


def test_tick_no_order_on_hold_signal(mock_iq, mock_consensus):
    """Consensus retorna HOLD → no se incrementa trade_count."""
    bot = BotOrchestrator(mock_iq, mock_consensus)
    bot._tick()
    assert bot._trade_count == 0
    mock_iq.buy.assert_not_called()


# ════════════════════════════════════════════════════════════════
# 3. Ejecución de Órdenes (Dry Run vs Real)
# ════════════════════════════════════════════════════════════════

def test_dry_run_increments_trade_count(mock_iq, mock_consensus):
    """En dry_run=True, se incrementa trade_count pero no se llama a iq.buy."""
    mock_consensus.evaluate.return_value = ConsensusResult(
        direction=Direction.CALL,
        agreement_ratio=1.0,
        avg_confidence=1.0,
        composite_score=1.0,
        participating=("S1",),
        agreeing=("S1",),
        signals=(),
        is_actionable=True
    )
    
    bot = BotOrchestrator(mock_iq, mock_consensus, dry_run=True)
    bot._tick()
    
    assert bot._trade_count == 1
    mock_iq.buy.assert_not_called()


def test_real_trade_execution(mock_iq, mock_consensus):
    """En dry_run=False, se llama a iq.buy."""
    mock_consensus.evaluate.return_value = ConsensusResult(
        direction=Direction.PUT,
        agreement_ratio=1.0,
        avg_confidence=1.0,
        composite_score=1.0,
        participating=("S1",),
        agreeing=("S1",),
        signals=(),
        is_actionable=True
    )
    
    bot = BotOrchestrator(mock_iq, mock_consensus, dry_run=False)
    bot._tick()
    
    assert bot._trade_count == 1
    # buy(amount, asset, action, duration)
    mock_iq.buy.assert_called_once_with(1.0, "EURUSD", "put", 60)



