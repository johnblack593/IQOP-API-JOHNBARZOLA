import threading
import time
import logging
from iqoptionapi.core.logger import get_logger
import iqoptionapi.core.config as config

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

    def _reconnect_with_backoff(self):
        """
        SPRINT 7/9: Reconexión delegada al ReconnectManager.
        """
        logger = get_logger(__name__)
        while True:
            try:
                # El manager maneja el delay y el límite de intentos (lanza MaxReconnectAttemptsError)
                self._reconnect_manager.wait()
                
                # Intentar refrescar el almacén de credenciales si es posible
                if hasattr(self, "_credentials"):
                    email, password = self._credentials
                    from iqoptionapi.core.security import CredentialStore
                    self._credential_store = CredentialStore(email, password)
                
                status, reason = self.connect()
                if status:
                    logger.info("Reconnected successfully.")
                    self._reconnect_manager.reset()
                    return True
                
            except Exception as e:
                # Capturamos MaxReconnectAttemptsError aquí
                from iqoptionapi.core.reconnect import MaxReconnectAttemptsError
                if isinstance(e, MaxReconnectAttemptsError):
                    logger.error("Reconnection failed: Max attempts exhausted.")
                    raise e
                logger.error("Reconnect attempt failed: %s", e)

    # --- Métodos migrados de stable_api.py ---

    def _wait_for_init_data(self, timeout: float = 25.0) -> bool:
        """
        Espera hasta que el servidor haya enviado initialization-data
        y el SDK tenga activos cargados en memoria.
        Retorna True si los datos llegaron, False si timeout.
        """
        logger = get_logger(__name__)
        deadline = time.time() + timeout
        while time.time() < deadline:
            init = getattr(self.api, 'api_option_init_all_result_v2', None)
            if init and isinstance(init, dict):
                binary_actives = init.get("binary", {}).get("actives", {})
                turbo_actives  = init.get("turbo",  {}).get("actives", {})
                if len(binary_actives) > 10 or len(turbo_actives) > 10:
                    logger.info(
                        "_wait_for_init_data: OK – binary=%d turbo=%d actives loaded",
                        len(binary_actives), len(turbo_actives)
                    )
                    return True
            time.sleep(0.5)
        logger.warning(
            "_wait_for_init_data: timeout after %.0fs – init data may be incomplete",
            timeout
        )
        return False

    def _auto_reconnect(self) -> None:
        """
        Auto-reconexión delegada a _reconnect_with_backoff.
        Llamado por WebsocketClient.on_close().
        """
        logger = get_logger(__name__)
        logger.info("Auto-reconnect triggered.")
        try:
            self._reconnect_with_backoff()
        except Exception as e:
            logger.error("Auto-reconnect: exception during connect(): %s", e)

    def _start_heartbeat_watchdog(self):
        """
        SPRINT 4: Inicia hilo que monitorea el heartbeat del WebSocket.
        """
        if hasattr(self, '_heartbeat_watchdog_active') and self._heartbeat_watchdog_active:
            return

        self._heartbeat_watchdog_active = True
        self._last_heartbeat = time.time()
        self._watchdog_stop = threading.Event()

        def watchdog_loop():
            get_logger(__name__).info("Heartbeat watchdog started.")
            while not self._watchdog_stop.wait(timeout=config.HEARTBEAT_CHECK_INTERVAL):
                try:
                    if not self.check_connect():
                        continue
                    
                    elapsed = time.time() - self._last_heartbeat
                    if elapsed > config.HEARTBEAT_TIMEOUT_SECS:
                        get_logger(__name__).warning(
                            "Heartbeat watchdog: %.0fs sin heartbeat — forzando reconexión",
                            elapsed
                        )
                        self._last_heartbeat = time.time()
                        t = threading.Thread(
                            target=self._auto_reconnect, daemon=True,
                            name="WatchdogReconnect"
                        )
                        t.start()
                except Exception as e:
                    get_logger(__name__).error("Heartbeat watchdog error: %s", e)
            get_logger(__name__).info("Heartbeat watchdog stopped.")

        self._watchdog_thread = threading.Thread(
            target=watchdog_loop, name="HeartbeatWatchdog", daemon=True
        )
        self._watchdog_thread.start()

    def _stop_heartbeat_watchdog(self):
        if hasattr(self, '_watchdog_stop'):
            self._watchdog_stop.set()
        if hasattr(self, '_watchdog_thread'):
            self._watchdog_thread.join(timeout=2.0)
        self._heartbeat_watchdog_active = False

    def check_connect(self):
        if not hasattr(self, "api") or self.api is None:
            return False
        if self.api.websocket is None:
            return False
        if self.api.websocket.sock is None:
            return False
        return self.api.websocket.sock.connected

    def change_balance(self, Balance_MODE):
        def set_id(bal_id):
            self.api.balance_id = bal_id
            self.api.balance_changed_event.set()

        real_id = None
        practice_id = None
        tournament_id = None

        for balance in self.get_balances():
            if balance["type"] == 1:
                real_id = balance["id"]
            if balance["type"] == 4:
                practice_id = balance["id"]
            if balance["type"] == 2:
                tournament_id = balance["id"]

        if Balance_MODE == "REAL":
            set_id(real_id)
        elif Balance_MODE == "PRACTICE":
            set_id(practice_id)
        elif Balance_MODE == "TOURNAMENT":
            set_id(tournament_id)
        else:
            get_logger(__name__).error("ERROR doesn't have this mode")
            exit(1)

    def reset_practice_balance(self):
        self.api.training_balance_reset_request_event.clear()
        self.api.reset_training_balance()
        is_ready = self.api.training_balance_reset_request_event.wait(timeout=config.TIMEOUT_BALANCE_RESET)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for training_balance_reset_request")
        return self.api.training_balance_reset_request
