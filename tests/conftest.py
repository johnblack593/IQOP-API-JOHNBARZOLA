"""
Configuración global de la suite de tests JCBV-NEXUS SDK v9.1.000
"""
import pytest
import sys, pathlib
import threading

# Agregar raíz del proyecto al path para imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Excluir carpetas que no son tests del auto-discovery
collect_ignore_glob = [
    "scratch/**",      # ← ya eliminada, dejar por si regresa
    "reports/**",      # ← ya eliminada, dejar por si regresa
    "fixtures/**",     # fixtures JSON no son tests
]

@pytest.fixture(scope="session")
def sdk_version():
    """Versión del SDK bajo test."""
    from iqoptionapi import __version__
    return __version__

@pytest.fixture
def mock_api():
    """Mock mínimo de la instancia IQ_Option para tests unitarios."""
    from unittest.mock import MagicMock
    api = MagicMock()
    api.websocket_is_connected = True
    api.account_type = "PRACTICE"
    
    # Eventos reales para que wait() y set() funcionen
    api.close_position_event = threading.Event()
    api.result_event = threading.Event()
    api.authenticated_event = threading.Event()
    api.ws_connected_event = threading.Event()
    api.position_event = threading.Event()
    api.positions_event = threading.Event()
    api.digital_option_placed_id_event = threading.Event()
    
    return api
