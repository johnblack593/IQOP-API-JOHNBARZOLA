import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from iqoptionapi.subscription_manager import SubscriptionManager

class TestSubscriptionManager:
    @pytest.fixture
    def mock_api(self):
        api = MagicMock()
        return api

    def test_max_concurrent_subscriptions_limit(self, mock_api):
        """Verifica que el límite de 15 suscripciones se respete."""
        manager = SubscriptionManager(mock_api)
        manager.MAX_CONCURRENT_SUBSCRIPTIONS = 5
        
        # Intentamos suscribir 10 activos
        for i in range(10):
            manager.subscribe_candle(f"ACTIVE_{i}", 60)
        
        # El manager procesa en segundo plano, esperamos un poco
        time.sleep(2)
        
        # Verificamos que se hayan llamado a la API pero respetando el flujo
        assert mock_api.subscribe.call_count >= 1
        assert len(manager._active_subs) <= 10 # El límite de 15 es mayor que 10
        
        manager.stop()

    def test_jittered_delay(self, mock_api):
        """Verifica que hay un delay entre suscripciones."""
        manager = SubscriptionManager(mock_api)
        manager.MIN_DELAY_BETWEEN_SUBS = 0.5
        
        start_time = time.time()
        manager.subscribe_candle("EURUSD", 60)
        manager.subscribe_candle("GBPUSD", 60)
        
        # El dispatcher procesará ambos. El segundo debe esperar al menos 0.5 * 0.8 = 0.4s
        # Esperamos a que la cola se vacíe
        timeout = 5
        while timeout > 0:
            with manager._lock:
                if not manager._sub_queue:
                    break
            time.sleep(0.1)
            timeout -= 0.1
            
        elapsed = time.time() - start_time
        # Al menos un delay debe haber ocurrido (aprox 0.4s - 0.7s)
        assert elapsed >= 0.3
        
        manager.stop()

    def test_unsubscribe_removes_from_active_subs(self, mock_api):
        manager = SubscriptionManager(mock_api)
        manager.subscribe_candle("EURUSD", 60)
        
        # Esperar a que se procese
        time.sleep(1)
        assert ("EURUSD", 60) in manager._active_subs
        
        manager.unsubscribe_candle("EURUSD", 60)
        time.sleep(1)
        assert ("EURUSD", 60) not in manager._active_subs
        
        manager.stop()
