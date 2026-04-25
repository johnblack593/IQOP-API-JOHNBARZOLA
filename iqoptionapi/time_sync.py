# iqoptionapi/time_sync.py
import time
import threading

class ServerClockSync:
    """Sincronizador de reloj servidor/local con compensación dinámica."""
    
    def __init__(self):
        self._offset_ms = 0.0
        self._local_ref = time.time()
        self._lock = threading.Lock()
    
    def update(self, server_timestamp_ms: int):
        """Llamar cuando se recibe un heartbeat o timestamp del servidor."""
        with self._lock:
            # server_timestamp_ms viene en milisegundos
            self._offset_ms = (server_timestamp_ms / 1000.0) - time.time()
            self._local_ref = time.time()
    
    def now(self) -> float:
        """Retorna el tiempo actual estimado del servidor en segundos epoch."""
        with self._lock:
            return time.time() + self._offset_ms
    
    def offset_seconds(self) -> float:
        with self._lock:
            return self._offset_ms

# Singleton para uso en stable_api.py y buy_blitz()
_clock = ServerClockSync()
