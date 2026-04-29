
import pytest
import threading
import time
from unittest.mock import MagicMock, patch
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.core.config import TIMEOUT_WS_DATA

class MockAPI:
    def __init__(self):
        self.candles = MagicMock()
        self.candles.candles_data = None
        self.candles_event = threading.Event()
        
        self.underlying_list_data = None
        self.underlying_list_data_event = threading.Event()
        
        self.profile = MagicMock()
        self.profile.msg = None
        self.profile_msg_event = threading.Event()
        
        self.order_data = None
        self.order_data_event = threading.Event()
        
        self.positions = None
        self.positions_event = threading.Event()

    def getcandles(self):
        return MagicMock()

    def get_digital_underlying(self):
        pass

    def get_order(self, *args):
        pass

    def get_positions(self, *args):
        pass

@pytest.fixture
def api_instance():
    # Mocking OP_code.ACTIVES
    with patch("iqoptionapi.stable_api.OP_code.ACTIVES", {"EURUSD": 1}):
        instance = IQ_Option("test@example.com", "password")
        instance.api = MockAPI()
        return instance

def test_get_candles_success(api_instance):
    def simulate_server_response():
        time.sleep(0.1)
        api_instance.api.candles.candles_data = [{"from": 123, "close": 1.1}]
        api_instance.api.candles_is_maxdict = True

    threading.Thread(target=simulate_server_response).start()
    
    result = api_instance.get_candles("EURUSD", 60, 10, time.time())
    assert result == [{"from": 123, "close": 1.1}]
    assert getattr(api_instance.api, "candles_is_maxdict", False) is True

def test_get_candles_timeout(api_instance):
    # Shorten timeout for test
    with patch("iqoptionapi.core.config.TIMEOUT_WS_DATA", 0.1):
        result = api_instance.get_candles("EURUSD", 60, 10, time.time())
        assert result is None

def test_get_digital_underlying_success(api_instance):
    def simulate_server_response():
        time.sleep(0.1)
        api_instance.api.underlying_list_data = {"underlying": ["EURUSD"]}
        api_instance.api.underlying_list_data_event.set()

    threading.Thread(target=simulate_server_response).start()
    
    result = api_instance.get_digital_underlying_list_data()
    assert result == {"underlying": ["EURUSD"]}

def test_get_order_success(api_instance):
    def simulate_server_response():
        time.sleep(0.1)
        api_instance.api.order_data = {"status": 2000, "msg": {"id": 123}}
        api_instance.api.order_data_event.set()

    threading.Thread(target=simulate_server_response).start()
    
    status, data = api_instance.get_order(123)
    assert status is True
    assert data == {"id": 123}


