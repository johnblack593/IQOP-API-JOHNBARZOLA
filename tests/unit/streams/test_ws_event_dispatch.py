
import pytest
import threading
import time
from collections import defaultdict
from unittest.mock import MagicMock
from iqoptionapi.ws.received.orders.option_closed import OptionClosed
from iqoptionapi.ws.received.positions.position_changed import PositionChanged
from iqoptionapi.ws.received.orders.socket_option_closed import SocketOptionClosed

class MockInternalAPI:
    """Mock para simular la estructura de IQOptionAPI."""
    def __init__(self):
        self.result_event_store = defaultdict(threading.Event)
        self.socket_option_closed_event = defaultdict(threading.Event)
        self.position_changed_event_store = defaultdict(threading.Event)
        self.socket_option_closed = {}
        self.order_async = defaultdict(lambda: defaultdict(dict))
        self.order_binary = {}
        self.buy_multi_option = {}
        self.position_changed = None

def test_option_closed_handler_reactive():
    """Prueba que OptionClosed notifica correctamente los eventos."""
    api = MockInternalAPI()
    handler = OptionClosed()
    order_id = 12345
    
    # 1. Simular mensaje "option" (Binary Result)
    message_option = {
        "name": "option",
        "msg": {
            "id": order_id,
            "win": "win",
            "amount": 10
        }
    }
    
    handler(api, message_option)
    assert api.result_event_store[order_id].is_set(), "result_event_store no se activó con 'option'"
    assert api.socket_option_closed_event[order_id].is_set(), "socket_option_closed_event no se activó con 'option'"
    assert api.socket_option_closed[order_id] == message_option
    
    # Reset
    api.result_event_store[order_id].clear()
    
    # 2. Simular mensaje "option-closed"
    message_closed = {
        "name": "option-closed",
        "msg": {
            "option_id": order_id,
            "win": "loose"
        }
    }
    handler(api, message_closed)
    assert api.result_event_store[order_id].is_set(), "result_event_store no se activó con 'option-closed'"

def test_position_changed_handler_reactive():
    """Prueba que PositionChanged notifica correctamente el cierre digital."""
    api = MockInternalAPI()
    handler = PositionChanged()
    order_id = 55555
    
    message = {
        "name": "position-changed",
        "microserviceName": "portfolio",
        "msg": {
            "source": "digital-options",
            "status": "closed",
            "raw_event": {
                "order_ids": [order_id]
            },
            "position": {
                "status": "closed"
            }
        }
    }
    
    handler(api, message)
    assert api.position_changed_event_store[order_id].is_set(), "position_changed_event_store no se activó"
    assert api.result_event_store[order_id].is_set(), "result_event_store no se activó para digital fallback"

def test_socket_option_closed_handler_reactive():
    """Prueba que SocketOptionClosed notifica ambos stores."""
    api = MockInternalAPI()
    handler = SocketOptionClosed()
    order_id = 77777
    
    message = {
        "name": "socket-option-closed",
        "msg": {
            "id": order_id
        }
    }
    
    handler(api, message)
    assert api.socket_option_closed_event[order_id].is_set()
    assert api.result_event_store[order_id].is_set()

def test_type_resilience():
    """Prueba que el sistema es resiliente a IDs como string."""
    api = MockInternalAPI()
    handler = OptionClosed()
    
    # Server envía string, pero robot espera int (o viceversa)
    handler(api, {"name": "option", "msg": {"id": "88888", "win": "win"}})
    
    # Debería estar guardado como int 88888
    assert 88888 in api.result_event_store
    assert api.result_event_store[88888].is_set()
