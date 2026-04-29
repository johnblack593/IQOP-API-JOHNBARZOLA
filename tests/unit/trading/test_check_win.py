"""
Tests unitarios para check_win*() sin conexión real a IQ Option.
Usa mocks para simular eventos WS que disparan resultados.
"""
import threading
import pytest
from unittest.mock import MagicMock, patch
from collections import defaultdict

def make_mock_api():
    """Crea un mock mínimo de IQ_Option con todos los atributos necesarios."""
    api = MagicMock()
    api.api.result_event_store = defaultdict(threading.Event)
    api.api.socket_option_closed_event = defaultdict(threading.Event)
    api.api.position_changed_event_store = defaultdict(threading.Event)
    api.api.socket_option_closed = {}
    api.api.listinfodata = {}
    return api

class TestCheckWin:
    def test_check_win_returns_none_on_timeout(self):
        """Si el evento no se dispara, check_win retorna None en timeout."""
        # Arrange
        from iqoptionapi.stable_api import IQ_Option
        # Mockear __init__ para evitar conexión real
        with patch.object(IQ_Option, '__init__', return_value=None):
            iq = IQ_Option.__new__(IQ_Option)
            iq.api = MagicMock()
            iq.api.result_event_store = defaultdict(threading.Event)
            iq.api.listinfodata = {}
            # Event NUNCA se dispara → debe retornar None
            result = iq._wait_result(
                order_id=99999,
                result_store=iq.api.listinfodata,
                event_store=iq.api.result_event_store,
                timeout=0.1  # timeout muy corto para el test
            )
        # Assert
        assert result is None

    def test_check_win_returns_result_when_event_fires(self):
        """Si el evento se dispara con datos, check_win retorna el resultado."""
        from iqoptionapi.stable_api import IQ_Option
        with patch.object(IQ_Option, '__init__', return_value=None):
            iq = IQ_Option.__new__(IQ_Option)
            iq.api = MagicMock()
            event_store = defaultdict(threading.Event)
            result_store = {}
            order_id = 12345
            expected_result = {"id": order_id, "result": "win", "win": 1.85}
            
            # Pre-crear el evento para evitar que _wait_result cree uno diferente
            event = event_store[order_id]
            
            # Simular que el WS handler dispara el evento con resultado
            def fire_event():
                import time
                time.sleep(0.05)
                result_store[order_id] = expected_result
                event.set()
            
            t = threading.Thread(target=fire_event)
            t.start()
            
            result = iq._wait_result(
                order_id=order_id,
                result_store=result_store,
                event_store=event_store,
                timeout=2.0
            )
            t.join()
        
        assert result == expected_result
        assert result["result"] == "win"
