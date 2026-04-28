import threading
import time
import logging
from iqoptionapi.logger import get_logger

class ManagementMixin:
    def sync_state_on_connect(self):
        """
        Sprint 5: Synchronize all active positions and pending orders.
        Blocks for up to 10 seconds to ensure state consistency.
        """
        get_logger(__name__).info("Syncing SDK state (positions/orders)...")
        
        # We request positions for common margin types
        instrument_types = ["crypto", "forex", "cfd"]
        
        self.api.positions_event.clear()
        
        # Bulk request
        for itype in instrument_types:
            self.api.get_positions(itype)
            
        # Wait for at least one response
        is_ready = self.api.positions_event.wait(timeout=10)
        
        if is_ready and self.api.positions:
            # The 'positions' message is a list of open positions
            positions_list = self.api.positions.get("msg", {}).get("positions", [])
            for pos in positions_list:
                pid = pos.get("id")
                if pid:
                    self.positions_state_data[pid] = pos
            get_logger(__name__).info(f"Sync complete: {len(self.positions_state_data)} positions found.")
        else:
            get_logger(__name__).warning("Sync state TIMEOUT or no positions found.")
            
        return self.positions_state_data

    def _start_token_refresh_worker(self, refresh_interval_hours=4):
        """
        SPRINT 6: Daemon thread que re-autentica antes de que el token expire.
        """
        def refresh_loop():
            get_logger(__name__).info("Token refresh worker started (Interval: %sh)", refresh_interval_hours)
            while not self._stop_event.wait(timeout=refresh_interval_hours * 3600):
                try:
                    if hasattr(self, '_credentials'):
                        email, password = self._credentials
                        get_logger(__name__).info("Executing background token refresh...")
                        # reconnect() already handles the flow and updates api.SSID
                        self.connect()
                    else:
                        get_logger(__name__).warning("Token refresh worker: No credentials stored.")
                        break
                except Exception as e:
                    get_logger(__name__).error("Token refresh failed: %s", e)

        t = threading.Thread(target=refresh_loop, name="TokenRefreshWorker", daemon=True)
        t.start()

    def _reconnect_with_backoff(self, max_attempts=10):
        """
        SPRINT 7: Reconexión con Exponential Backoff y Jitter.
        """
        import random
        delay = 1.0
        for attempt in range(max_attempts):
            jitter = random.uniform(0.8, 1.2)
            get_logger(__name__).info(
                "Reconnect attempt %d/%d — waiting %.2fs", 
                attempt + 1, max_attempts, delay * jitter
            )
            time.sleep(delay * jitter)
            
            # Reset credential store for fresh attempt
            if hasattr(self, "_credentials"):
                email, password = self._credentials
                from iqoptionapi.security import CredentialStore
                self._credential_store = CredentialStore(email, password)
            
            status, reason = self.connect()
            if status:
                get_logger(__name__).info("Reconnected successfully.")
                return True
            
            delay = min(delay * 2, 60.0)  # Cap at 60s
            
        return False
