"""
Gestor centralizado de suscripciones WS que emula el comportamiento
del browser de IQ Option para evitar rate-limiting y baneos.
"""

import threading
import time
from collections import deque
from iqoptionapi.core.logger import get_logger

class SubscriptionManager:
    """
    Gestor centralizado de suscripciones WS que emula el comportamiento
    del browser de IQ Option para evitar rate-limiting y baneos.
    """
    
    MAX_SUBSCRIPTIONS_PER_SECOND = 3  # Valor inicial seguro
    MIN_DELAY_BETWEEN_SUBS = 0.4      # segundos
    MAX_CONCURRENT_SUBSCRIPTIONS = 15 # imita el límite del navegador real
    
    def __init__(self, api_instance):
        self._api = api_instance
        self._active_subs = {}      # {(active, size): timestamp}
        self._sub_queue = deque()    # cola de pendientes: (action, active, size, priority)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._dispatcher_thread = threading.Thread(target=self._dispatch_loop, daemon=True, name="SubManager")
        self._dispatcher_thread.start()
        self.logger = get_logger(__name__)

    def subscribe_candle(self, active, size, priority=0):
        """
        Encola una suscripción de velas.
        priority=0 normal, 1 alta (se inserta al principio de la cola).
        """
        with self._lock:
            item = ("subscribe", active, size)
            if priority > 0:
                self._sub_queue.appendleft(item)
            else:
                self._sub_queue.append(item)
        self.logger.debug("Enqueued subscription for %s (size %s) priority %s", active, size, priority)

    def subscribe_candles_batch(self, actives, size):
        """
        Suscribe múltiples activos con delays humanizados entre cada uno.
        """
        for active in actives:
            self.subscribe_candle(active, size)

    def unsubscribe_candle(self, active, size):
        """
        Encola una desuscripción de velas.
        """
        with self._lock:
            self._sub_queue.append(("unsubscribe", active, size))
        self.logger.debug("Enqueued unsubscription for %s (size %s)", active, size)

    def subscribe_positions(self, instrument_type, priority=0):
        """Encola suscripción a cambios de posición."""
        with self._lock:
            item = ("subscribe_positions", instrument_type, None)
            if priority > 0:
                self._sub_queue.appendleft(item)
            else:
                self._sub_queue.append(item)
        self.logger.debug("Enqueued positions subscription for %s", instrument_type)

    def subscribe_orders(self, instrument_type, priority=0):
        """Encola suscripción a cambios de órdenes."""
        with self._lock:
            item = ("subscribe_orders", instrument_type, None)
            if priority > 0:
                self._sub_queue.appendleft(item)
            else:
                self._sub_queue.append(item)
        self.logger.debug("Enqueued orders subscription for %s", instrument_type)

    def subscribe_instruments_realtime(self, instrument_type, priority=0):
        """Encola suscripción a instrumentos en tiempo real."""
        with self._lock:
            item = ("subscribe_instruments_realtime", instrument_type, None)
            if priority > 0:
                self._sub_queue.appendleft(item)
            else:
                self._sub_queue.append(item)
        self.logger.debug("Enqueued instruments-realtime subscription for %s", instrument_type)

    def get_active_count(self):
        with self._lock:
            return len(self._active_subs)

    def _dispatch_loop(self):
        """
        Thread daemon que procesa la cola con rate limiting humanizado.
        """
        while not self._stop_event.is_set():
            item = None
            with self._lock:
                if self._sub_queue:
                    item = self._sub_queue.popleft()
            
            if item:
                action, active, size = item
                try:
                    if action == "subscribe":
                        self._api.subscribe_instruments_candles(active, size)
                        with self._lock:
                            self._active_subs[(active, size)] = time.time()
                    elif action == "unsubscribe":
                        self._api.unsubscribe_instruments_candles(active, size)
                        with self._lock:
                            self._active_subs.pop((active, size), None)
                    elif action == "subscribe_positions":
                        # names: "position-changed", "digital-options.position-changed", etc.
                        # generic fallback
                        self._api.subscribe_position_changed("position-changed", active, None)
                    elif action == "subscribe_orders":
                        self._api.portfolio("subscribeMessage", "portfolio.order-changed", active)
                    elif action == "subscribe_instruments_realtime":
                        self._api.subscribe_instruments_list(active)
                    
                    # Delay humanizado con jitter (A4)
                    import random
                    jitter = random.uniform(0.8, 1.5)
                    time.sleep(self.MIN_DELAY_BETWEEN_SUBS * jitter)
                except Exception as e:
                    self.logger.error("Error in subscription dispatcher for %s %s: %s", action, active, e)
            else:
                # Esperar si la cola está vacía
                time.sleep(0.1)

    def stop(self):
        self._stop_event.set()
        if self._dispatcher_thread.is_alive():
            self._dispatcher_thread.join(timeout=1.0)

