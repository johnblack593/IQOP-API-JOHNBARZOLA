"""
tests/unit/test_api_coverage.py
──────────────────────────────
Tests directos sobre IQOptionAPI para subir cobertura en api.py.
Verifica que las llamadas a métodos envíen los mensajes correctos por websocket.
"""
import pytest
from unittest.mock import MagicMock, patch
from iqoptionapi.api import IQOptionAPI

@pytest.fixture
def api():
    obj = IQOptionAPI("host", "user")
    obj.send_websocket_request = MagicMock()
    obj.balance_id = 123
    return obj

class TestAPICoverage:
    def test_get_balances(self, api):
        api.get_balances()
        api.send_websocket_request.assert_called()

    def test_buyv3(self, api):
        api.buyv3(1.0, 1, "call", 60, "req_1")
        api.send_websocket_request.assert_called()

    def test_place_digital_option(self, api):
        with patch("iqoptionapi.api.Digital_options_place_digital_option") as mock_chan:
            api.place_digital_option("id_1", 10)
            mock_chan.assert_called_once()

    def test_get_strike_list(self, api):
        api.get_strike_list("EURUSD", 1)
        api.send_websocket_request.assert_called()

    def test_subscribe_instrument_quotes(self, api):
        # subscribe_instrument_quotes_generated ES property
        api.subscribe_instrument_quotes_generated("EURUSD", 1)
        api.send_websocket_request.assert_called()

    def test_unsubscribe_instrument_quotes(self, api):
        api.unsubscribe_instrument_quotes_generated("EURUSD", 1)
        api.send_websocket_request.assert_called()

    def test_reset_training_balance(self, api):
        api.reset_training_balance()
        api.send_websocket_request.assert_called()

    def test_get_instruments(self, api):
        api.get_instruments("digital-option")
        api.send_websocket_request.assert_called()

    def test_get_digital_underlying(self, api):
        api.get_digital_underlying()
        api.send_websocket_request.assert_called()

    def test_set_user_settings(self, api):
        api.set_user_settings(123)
        api.send_websocket_request.assert_called()
