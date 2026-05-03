"""
tests/unit/test_stable_api_coverage.py
──────────────────────────────────────
Tests para stable_api.py enfocados en subir cobertura.
"""
import pytest
import threading
from unittest.mock import MagicMock, patch
from iqoptionapi.stable_api import IQ_Option

@pytest.fixture
def iq():
    with patch("iqoptionapi.api.IQOptionAPI") as mock_api_class:
        mock_api = mock_api_class.return_value
        mock_api.timesync.server_timestamp = 1600000000
        
        # Data for balances
        BALANCES_DATA = [{"id": 1, "amount": 1000.0, "type": 1}, {"id": 2, "amount": 5000.0, "type": 4}]
        
        # Mock para balances
        mock_api.balance_id = 1
        mock_api.balances_raw_event = threading.Event()
        
        def mock_get_balances():
            # stable_api.py wipes balances_raw before calling this
            mock_api.balances_raw = {"msg": BALANCES_DATA}
            mock_api.balances_raw_event.set()
            return BALANCES_DATA
        mock_api.get_balances.side_effect = mock_get_balances
        
        # Mocks para eventos
        mock_api.order_data_event = threading.Event()
        mock_api.order_data_event.set()
        mock_api.result_event = threading.Event()
        
        # Mocks para canales
        mock_api.getcandles = MagicMock(return_value=MagicMock())
        
        def mock_buyv3(price, active, action, expired, req_id):
            mock_api.buy_multi_option[str(req_id)] = {"id": 12345}
            mock_api.result_event.set()
        mock_api.buyv3.side_effect = mock_buyv3
        
        mock_api.buy_multi_option = {}
        mock_api.result = True
        
        # Mocks para propiedades que retornan canales
        mock_api.subscribe_instrument_quotes_generated = MagicMock()
        mock_api.unsubscribe_instrument_quotes_generated = MagicMock()
        
        iq_obj = IQ_Option("test@test.com", "password")
        iq_obj.api = mock_api
        return iq_obj

class TestStableAPICore:
    def test_get_server_timestamp(self, iq):
        assert iq.get_server_timestamp() == 1600000000

    def test_change_balance(self, iq):
        iq.change_balance("PRACTICE")
        assert iq.api.balance_id == 2

    def test_get_balance(self, iq):
        assert iq.get_balance() == 1000.0

    def test_buy_binary_success(self, iq):
        with patch("iqoptionapi.mixins.orders_mixin.randint", return_value=123):
            status, order_id = iq.buy(10, "EURUSD", "call", 1)
            assert status is True
            assert order_id == 12345

    def test_buy_digital_success(self, iq):
        iq.api.place_digital_option_v2.return_value = "req1"
        iq.api.digital_option_placed_id = {"req1": 999}
        iq.api.digital_option_placed_id_event = threading.Event()
        iq.api.digital_option_placed_id_event.set()
        
        status, order_id = iq.buy_digital_spot("EURUSD", 10, "call", 1)
        assert status is True
        assert order_id == 999

    def test_check_win_v3_success(self, iq):
        with patch.object(iq, '_wait_result', return_value={"win": "win"}):
            status, res = iq.check_win_v3(123)
            assert status is True
            assert res == "win"

    def test_get_candles_logic(self, iq):
        raw_candles = [{"from": 1, "close": 1.1}]
        iq.api.candles.candles_data = raw_candles
        
        def side_effect(*args, **kwargs):
            iq.api.candles_is_maxdict = True
            return MagicMock()
        
        iq.api.getcandles.side_effect = side_effect
        
        candles = iq.get_candles("EURUSD", 60, 1, 1600000000)
        assert candles == raw_candles

    def test_subscribe_strike_list(self, iq):
        iq.subscribe_strike_list("EURUSD", 1)
        iq.api.subscribe_instrument_quotes_generated.assert_called_with("EURUSD", 1)

    def test_unsubscribe_strike_list(self, iq):
        iq.unsubscribe_strike_list("EURUSD", 1)
        iq.api.unsubscribe_instrument_quotes_generated.assert_called_with("EURUSD", 1)
