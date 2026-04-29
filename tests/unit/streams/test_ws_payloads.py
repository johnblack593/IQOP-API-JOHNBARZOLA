import time
import logging
from iqoptionapi.stable_api import IQ_Option
import pytest
import os
from iqoptionapi.api import IQOptionAPI

# Mock or Real credentials depending on environment
# For this verification, we assume the user has a valid session or we use a dry-run style approach.
# However, since I have the browser session, I can see the user is logged in.

@pytest.fixture
def api():
    # Use environment variables or placeholders
    email = os.getenv("IQ_EMAIL", "johnbarzola@example.com")
    password = os.getenv("IQ_PASSWORD", "password123")
    api = IQ_Option(email, password)
    # api.connect() # Not connecting in unit test to avoid side effects
    return api

def test_blitz_payload_generation(api, mocker):
    # Initialize the underlying API instance manually since we aren't calling connect()
    # Mock OP_code.ACTIVES to avoid ValueError: Unknown active
    import iqoptionapi.core.constants as OP_code
    OP_code.ACTIVES["EURUSD"] = 1
    
    api.api = IQOptionAPI("ws.iqoption.com", "test@test.com")
    api.api.result_event_store = {} # Needed for some result waits
    
    # Mock send_websocket_request to capture the payload
    spy = mocker.spy(api.api, "send_websocket_request")
    
    # Set a dummy balance_id
    api.api.balance_id = 987654321
    
    # Trigger buy_blitz
    # buy_blitz(active, amount, action, current_price, duration=5)
    api.buy_blitz("EURUSD", 1, "call", 1.171165, duration=5)
    
    # Assert
    assert spy.called
    name, data, request_id = spy.call_args[0]
    assert name == "sendMessage"
    assert data["name"] == "binary-options.open-option"
    assert data["version"] == "2.0"
    assert data["body"]["active_id"] == 1 # EURUSD
    assert data["body"]["option_type_id"] == 12 # Blitz
    assert data["body"]["value"] == 1171165 # Multiplied price
    assert data["body"]["price"] == 1.0

def test_pending_order_payload_generation(api, mocker):
    import iqoptionapi.core.constants as OP_code
    OP_code.ACTIVES["EURUSD"] = 1
    api.api = IQOptionAPI("ws.iqoption.com", "test@test.com")
    spy = mocker.spy(api.api, "send_websocket_request")
    api.api.balance_id = 987654321
    
    # place_pending_order(active, instrument_type, side, amount, leverage, stop_price, ...)
    api.place_pending_order("EURUSD", "forex", "buy", 1, 300, 1.17200)
    
    assert spy.called
    name, data, request_id = spy.call_args[0]
    assert data["name"] == "marginal-forex.place-stop-order"
    assert data["body"]["instrument_id"] == "mf.1"
    assert data["body"]["stop_price"] == "1.172"
