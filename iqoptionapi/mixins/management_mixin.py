import threading
import time
from iqoptionapi.core.logger import get_logger
import iqoptionapi.core.config as config
from iqoptionapi.core.utils import nested_dict

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
        SPRINT 11: Reconexión protegida por CircuitBreaker.
        """
        logger = get_logger(__name__)
        from iqoptionapi.circuit_breaker import CircuitBreakerState

        while True:
            # SPRINT 11: Guard ante circuito abierto (ej: por baneo o fallos repetidos)
            if hasattr(self, 'circuit_breaker') and self.circuit_breaker.state == CircuitBreakerState.OPEN:
                logger.error("CircuitBreaker is OPEN. Reconnection aborted to prevent further damage.")
                return False

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
                    if hasattr(self, 'circuit_breaker'):
                        self.circuit_breaker.record_success()
                    return True
                else:
                    logger.warning("Connect failed during backoff: %s", reason)
                    if hasattr(self, 'circuit_breaker'):
                        self.circuit_breaker.record_failure(reason)
                
            except Exception as e:
                # Capturamos MaxReconnectAttemptsError aquí
                from iqoptionapi.core.reconnect import MaxReconnectAttemptsError
                if isinstance(e, MaxReconnectAttemptsError):
                    logger.error("Reconnection failed: Max attempts exhausted.")
                    if hasattr(self, 'circuit_breaker'):
                        self.circuit_breaker.record_failure("Max reconnect attempts reached")
                    raise e
                
                logger.error("Reconnect attempt failed: %s", e)
                if hasattr(self, 'circuit_breaker'):
                    self.circuit_breaker.record_failure(str(e))

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
                    
                    # SPRINT 14: Sincronizar con timestamp de la API interna
                    api_hb = getattr(self.api, 'last_heartbeat_timestamp', self._last_heartbeat)
                    elapsed = time.time() - api_hb
                    
                    if elapsed > config.HEARTBEAT_TIMEOUT_SECS:
                        get_logger(__name__).warning(
                            "Heartbeat watchdog: %.0fs sin heartbeat — forzando reconexión",
                            elapsed
                        )
                        # Actualizar para evitar spam de reconexión
                        setattr(self.api, 'last_heartbeat_timestamp', time.time())
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
        if hasattr(self, '_watchdog_stop') and self._watchdog_stop:
            self._watchdog_stop.set()
        if hasattr(self, '_watchdog_thread') and self._watchdog_thread:
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

    def __init_management__(self):
        self._heartbeat_thread = None
        self._watchdog_thread = None
        self._reconnect_stop_event = threading.Event()
        self._heartbeat_watchdog_active = False
        self._last_heartbeat = time.time()


    def get_all_init(self):
        'Solicita initialization-data. Una sola llamada WS por sesión.'
        if (self.api.api_option_init_all_result is not None):
            return self.api.api_option_init_all_result
        self.api.api_option_init_all_result_event.clear()
        self.api.get_api_option_init_all()
        is_ready = self.api.api_option_init_all_result_event.wait(timeout=config.TIMEOUT_ALL_INIT)
        if (not is_ready):
            get_logger(__name__).warning('Timeout waiting for get_all_init')
        return self.api.api_option_init_all_result

    def get_all_init_v2(self):
        'Solicita initialization-data v2. Una sola llamada WS por sesión.'
        if (self.api.api_option_init_all_result_v2 is not None):
            return self.api.api_option_init_all_result_v2
        if (self.check_connect() == False):
            self.connect()
        self.api.api_option_init_all_result_v2_event.clear()
        self.api.get_api_option_init_all_v2()
        is_ready = self.api.api_option_init_all_result_v2_event.wait(timeout=config.TIMEOUT_ALL_INIT)
        if (not is_ready):
            get_logger(__name__).warning('Timeout waiting for get_all_init_v2')
        return self.api.api_option_init_all_result_v2

    def __get_binary_open(self):
        v2_data = self.get_all_init_v2()
        v1_data = self.get_all_init()
        binary_list = ['binary', 'turbo', 'blitz']
        if v2_data:
            for option in binary_list:
                if (option in v2_data):
                    for actives_id in v2_data[option]['actives']:
                        active = v2_data[option]['actives'][actives_id]
                        name = str(active['name']).split('.')[1]
                        self.OPEN_TIME[option][name]['open'] = (active['enabled'] and (not active.get('is_suspended', False)))
        if (v1_data and v1_data.get('result')):
            res = v1_data['result']
            for option in binary_list:
                if (option in res):
                    for actives_id in res[option]['actives']:
                        active = res[option]['actives'][actives_id]
                        name = str(active['name']).split('.')[1]
                        self.OPEN_TIME[option][name]['open'] = (active['enabled'] and (not active.get('is_suspended', False)))

    def __get_digital_open(self):
        digital_data = []
        for _ in range(3):
            data = self.get_digital_underlying_list_data()
            if (isinstance(data, dict) and ('underlying' in data)):
                digital_data = data.get('underlying', [])
            elif isinstance(data, list):
                digital_data = data
            get_logger(__name__).debug('__get_digital_open: data=%s', digital_data)
            if digital_data:
                break
            time.sleep(2)
        for digital in digital_data:
            name = digital.get('underlying')
            if (not name):
                continue
            schedule = digital.get('schedule', [])
            self.OPEN_TIME['digital'][name]['open'] = False
            for schedule_time in schedule:
                start = schedule_time.get('open', 0)
                end = schedule_time.get('close', 0)
                if (start < time.time() < end):
                    self.OPEN_TIME['digital'][name]['open'] = True
        if (not digital_data):
            try:
                insts = self.get_instruments('digital-option')
                if (insts and ('instruments' in insts)):
                    for detail in insts['instruments']:
                        n = detail.get('name')
                        if (not n):
                            continue
                        if ('.' in n):
                            n = n.split('.')[1]
                        self.OPEN_TIME['digital'][n]['open'] = any(((s.get('open', 0) < time.time() < s.get('close', 0)) for s in detail.get('schedule', [])))
            except Exception:
                pass
        if (not any((v.get('open') for v in self.OPEN_TIME['digital'].values()))):
            get_logger(__name__).info('Digital discovery failed, mirroring binary/turbo asset availability')
            for cat in ['binary', 'turbo']:
                for (asset, info) in self.OPEN_TIME.get(cat, {}).items():
                    if info.get('open'):
                        self.OPEN_TIME['digital'][asset]['open'] = True

    def __get_other_open(self):
        instrument_list = ['cfd', 'forex', 'crypto', 'stocks', 'commodities', 'indices', 'etf']
        for instruments_type in instrument_list:
            if (instruments_type != instrument_list[0]):
                import random
                time.sleep(random.uniform((config.STEALTH_INSTRUMENT_REQUEST_DELAY * 0.8), (config.STEALTH_INSTRUMENT_REQUEST_DELAY * 1.2)))
            ins_data = []
            for _ in range(3):
                result = self.get_instruments(instruments_type)
                if (isinstance(result, dict) and ('instruments' in result)):
                    ins_data = result.get('instruments', [])
                elif isinstance(result, list):
                    ins_data = result
                elif hasattr(result, 'get'):
                    ins_data = result.get('instruments', [])
                if ins_data:
                    break
                time.sleep(2)
            for detail in ins_data:
                name = detail.get('name')
                if (not name):
                    continue
                if ('.' in name):
                    name = name.split('.')[1]
                schedule = detail.get('schedule', [])
                self.OPEN_TIME[instruments_type][name]['open'] = False
                for schedule_time in schedule:
                    start = schedule_time.get('open', 0)
                    end = schedule_time.get('close', 0)
                    if (start < time.time() < end):
                        self.OPEN_TIME[instruments_type][name]['open'] = True

    def get_all_open_time(self):
        self.OPEN_TIME = nested_dict(3, dict)
        binary = threading.Thread(target=self.__get_binary_open)
        digital = threading.Thread(target=self.__get_digital_open)
        other = threading.Thread(target=self.__get_other_open)
        (binary.start(), digital.start(), other.start())
        (binary.join(), digital.join(), other.join())
        return self.OPEN_TIME
