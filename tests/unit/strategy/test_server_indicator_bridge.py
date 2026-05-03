"""
Unit tests for ServerIndicatorBridge.
"""

import pytest
from iqoptionapi.strategy.signal import Direction
from iqoptionapi.strategy.server_indicator_bridge import ServerIndicatorBridge


def test_empty_bridge_is_empty():
    """ServerIndicatorBridge(None).is_empty() == True."""
    assert ServerIndicatorBridge(None).is_empty() is True
    assert ServerIndicatorBridge({}).is_empty() is True


def test_error_response_is_empty():
    """is_empty() == True para respuesta de error del servidor."""
    raw = {
        "code": "no_technical_indicator_available",
        "message": "Market is closed or no data"
    }
    bridge = ServerIndicatorBridge(raw)
    assert bridge.is_empty() is True


def test_valid_bridge_not_empty():
    """is_empty() == False si hay al menos un indicador."""
    raw = {"rsi": {"signal": "BUY", "value": 67.4}}
    bridge = ServerIndicatorBridge(raw)
    assert bridge.is_empty() is False


def test_get_signal_buy_returns_call():
    """signal='BUY' -> Direction.CALL."""
    raw = {"rsi": {"signal": "BUY", "value": 67.4}}
    bridge = ServerIndicatorBridge(raw)
    assert bridge.get_signal("rsi") == Direction.CALL


def test_get_signal_sell_returns_put():
    """signal='SELL' -> Direction.PUT."""
    raw = {"ma": {"signal": "SELL", "value": 1.0850}}
    bridge = ServerIndicatorBridge(raw)
    assert bridge.get_signal("ma") == Direction.PUT


def test_get_signal_neutral_returns_hold():
    """signal='NEUTRAL' -> Direction.HOLD."""
    raw = {"ema": {"signal": "NEUTRAL", "value": 1.0855}}
    bridge = ServerIndicatorBridge(raw)
    assert bridge.get_signal("ema") == Direction.HOLD


def test_get_signal_case_insensitive():
    """signal='buy' -> Direction.CALL."""
    raw = {"rsi": {"signal": "buy"}}
    bridge = ServerIndicatorBridge(raw)
    assert bridge.get_signal("RSI") == Direction.CALL


def test_get_signal_missing_indicator_returns_none():
    """Indicador inexistente -> None."""
    bridge = ServerIndicatorBridge({"rsi": {"signal": "BUY"}})
    assert bridge.get_signal("macd") is None


def test_get_value_returns_float():
    """get_value() retorna float correctamente."""
    raw = {"rsi": {"signal": "BUY", "value": 67.4}}
    bridge = ServerIndicatorBridge(raw)
    assert bridge.get_value("rsi") == pytest.approx(67.4)


def test_get_value_nested_field():
    """get_value() con campos específicos."""
    raw = {"stochastic": {"signal": "BUY", "k": 82.1, "d": 71.3}}
    bridge = ServerIndicatorBridge(raw)
    assert bridge.get_value("stochastic", "k") == pytest.approx(82.1)
    assert bridge.get_value("stochastic", "d") == pytest.approx(71.3)


def test_consensus_direction_majority_buy():
    """3 BUY, 1 SELL -> Direction.CALL."""
    raw = {
        "rsi": {"signal": "BUY"},
        "ma": {"signal": "BUY"},
        "ema": {"signal": "BUY"},
        "macd": {"signal": "SELL"}
    }
    bridge = ServerIndicatorBridge(raw)
    assert bridge.consensus_direction() == Direction.CALL


def test_as_dict_structure():
    """Verificar estructura de as_dict()."""
    raw = {
        "rsi": {"signal": "BUY", "value": 67.4},
        "stochastic": {"signal": "NEUTRAL", "k": 82.1, "d": 71.3}
    }
    bridge = ServerIndicatorBridge(raw)
    res = bridge.as_dict()
    
    assert "available" in res
    assert "consensus" in res
    assert "signals" in res
    assert "values" in res
    
    assert "rsi" in res["available"]
    assert res["signals"]["rsi"] == "BUY"
    assert res["values"]["rsi"]["value"] == 67.4
    assert res["values"]["stochastic"]["k"] == 82.1
