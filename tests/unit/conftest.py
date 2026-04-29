import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from collections import defaultdict
import threading

@pytest.fixture
def mock_iq(mock_api):
    """
    Fixture completo: instancia IQ_Option con self.api mockeado.
    Cubre los módulos: orders, positions, streams, management.
    """
    from iqoptionapi.stable_api import IQ_Option
    from iqoptionapi.core.ratelimit import TokenBucket
    from iqoptionapi.core.idempotency import IdempotencyRegistry
    
    with patch.object(IQ_Option, '__init__', return_value=None):
        iq = IQ_Option.__new__(IQ_Option)
        iq.api = mock_api
        
        # Managers y Registries (usando spec para que isinstance pase)
        iq._idempotency = MagicMock(spec=IdempotencyRegistry)
        iq._idempotency.register.return_value = "test_request_id"
        
        iq._order_bucket = MagicMock(spec=TokenBucket)
        iq._order_bucket.consume.return_value = True
        
        from iqoptionapi.validator import Validator
        iq.validator = MagicMock(spec=Validator)
        iq.validator.validate_order.return_value = (True, "ok")
        
        iq.logger = MagicMock()
        
        # Data stores (v9.0.000)
        iq.api.socket_option_closed = {}
        iq.api.digital_option_closed = {}
        iq.api.listinfodata = {}
        iq.api.buy_multi_option = {}
        iq.api.digital_option_placed_id = {}
        
        # Event stores para check_win* (per-ID events)
        iq.api.result_event_store = defaultdict(threading.Event)
        iq.api.socket_option_closed_event = defaultdict(threading.Event)
        iq.api.digital_option_closed_event = defaultdict(threading.Event)
        iq.api.position_changed_event_store = defaultdict(
            threading.Event
        )
        
        # Atributos de estado necesarios
        iq.email = "test@example.com"
        iq.api.timesync = MagicMock()
        iq.api.timesync.server_timestamp = 1600000000
        
        # Mock de session scheduler
        iq.session_scheduler = MagicMock()
        iq.session_scheduler.is_trading_time.return_value = True
        
        # Mock de SubscriptionManager
        iq.subscription_manager = MagicMock()
        
    return iq

@pytest.fixture
def token_bucket():
    """TokenBucket real (sin mock) para tests de rate limiting."""
    from iqoptionapi.core.ratelimit import TokenBucket
    return TokenBucket(capacity=5, refill_rate=1.0)
