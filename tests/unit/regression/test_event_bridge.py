"""
Regresión Sprint 14: Los WS handlers deben disparar eventos
en result_event_store / socket_option_closed_event /
position_changed_event_store al recibir mensajes de cierre.
"""
import threading
from collections import defaultdict
from unittest.mock import MagicMock
import pytest
import time

def _build_mock_api():
    api = MagicMock()
    api.result_event_store = defaultdict(threading.Event)
    api.position_changed_event_store = defaultdict(threading.Event)
    api.socket_option_closed_event = defaultdict(threading.Event)
    api.game_betinfo = {}
    api.socket_option_closed = {}
    api.order_async = defaultdict(dict)
    api.order_binary = {}
    api.position_changed_data = {}
    return api

class TestOptionClosedBridge:
    def test_sets_result_event_on_win(self):
        from iqoptionapi.ws.received.orders.option_closed import OptionClosed
        api = _build_mock_api()
        handler = OptionClosed()
        order_id = "123"
        msg = {
            "name": "option",
            "msg": {
                "id": order_id,
                "status": "win",
                "profit_amount": 100
            }
        }
        handler(api, msg)
        assert api.result_event_store[int(order_id)].is_set(), (
            "option_closed no disparó result_event_store tras win"
        )

    def test_sets_result_event_on_loose(self):
        from iqoptionapi.ws.received.orders.option_closed import OptionClosed
        api = _build_mock_api()
        handler = OptionClosed()
        order_id = "456"
        msg = {
            "name": "option",
            "msg": {
                "id": order_id,
                "status": "loose",
                "profit_amount": 0
            }
        }
        handler(api, msg)
        assert api.result_event_store[int(order_id)].is_set()

class TestSocketOptionClosedBridge:
    def test_sets_socket_event(self):
        from iqoptionapi.ws.received.orders.socket_option_closed import (
            SocketOptionClosed
        )
        api = _build_mock_api()
        handler = SocketOptionClosed()
        order_id = "789"
        msg = {"name": "socket-option-closed",
               "msg": {"id": order_id}}
        handler(api, msg)
        assert api.socket_option_closed_event[int(order_id)].is_set()

class TestPositionChangedBridge:
    def test_sets_event_on_closed_status(self):
        from iqoptionapi.ws.received.positions.position_changed import (
            PositionChanged
        )
        api = _build_mock_api()
        handler = PositionChanged()
        position_id = "001"
        msg = {
            "name": "position-changed",
            "msg": {
                "id": position_id,
                "status": "closed",
                "close_profit": 50.0
            }
        }
        handler(api, msg)
        assert api.position_changed_event_store[int(position_id)].is_set()

class TestCheckWinEndToEnd:
    """
    Simula el flujo completo: buy → WS message → check_win retorna.
    No requiere conexión real. El evento se dispara en un thread.
    """
    def test_check_win_resolves_before_timeout(self):
        from iqoptionapi.stable_api import IQ_Option
        # Mocking IQ_Option slightly to avoid real connection
        iq = MagicMock(spec=IQ_Option)
        iq.api = _build_mock_api()
        
        # We need the real _wait_result but on our mock
        from iqoptionapi.stable_api import IQ_Option as RealIQ
        iq._wait_result = RealIQ._wait_result.__get__(iq, IQ_Option)
        
        # We need the real check_win but on our mock
        from iqoptionapi.mixins.orders_mixin import OrdersMixin
        iq.check_win = OrdersMixin.check_win.__get__(iq, IQ_Option)

        order_id = 1001

        def _simulate_ws_response():
            time.sleep(0.2)
            iq.api.game_betinfo[order_id] = "win"
            iq.api.result_event_store[order_id].set()

        t = threading.Thread(target=_simulate_ws_response, daemon=True)
        t.start()
        
        result = iq.check_win(order_id, timeout=5.0)
        assert result == "win", f"check_win retornó {result!r} en lugar de 'win'"

    def test_check_win_still_returns_none_on_real_timeout(self):
        from iqoptionapi.stable_api import IQ_Option
        iq = MagicMock(spec=IQ_Option)
        iq.api = _build_mock_api()
        from iqoptionapi.stable_api import IQ_Option as RealIQ
        iq._wait_result = RealIQ._wait_result.__get__(iq, IQ_Option)
        from iqoptionapi.mixins.orders_mixin import OrdersMixin
        iq.check_win = OrdersMixin.check_win.__get__(iq, IQ_Option)
        
        result = iq.check_win(2002, timeout=0.1)
        assert result is None
