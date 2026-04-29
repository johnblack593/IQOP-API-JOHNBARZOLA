# python
from iqoptionapi.api import IQOptionAPI
import iqoptionapi.core.constants as OP_code
import iqoptionapi.country_id as Country
import threading
import time
import json
from iqoptionapi.core.logger import get_logger
from iqoptionapi.core.reconnect import ReconnectManager
from iqoptionapi.core.idempotency import IdempotencyRegistry
from iqoptionapi.core.security import CredentialStore
from iqoptionapi.core.ratelimit import TokenBucket, RateLimitExceededError, rate_limited
from iqoptionapi.http.session import close_shared_session
import iqoptionapi.core.config as config
import iqoptionapi
import logging
import operator
from collections import deque, defaultdict
from iqoptionapi.core.utils import nested_dict
from iqoptionapi.expiration import get_remaning_time
from iqoptionapi.mixins import OrdersMixin, PositionsMixin, StreamsMixin, ManagementMixin




class IQ_Option(OrdersMixin, PositionsMixin, StreamsMixin, ManagementMixin):
    __version__ = iqoptionapi.__version__

    def __init__(self, email, password, active_account_type="PRACTICE"):
        # SPRINT 7: Structured Logging Config
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        self._stop_event = threading.Event()
        
        # --- Base Infrastructure ---
        from iqoptionapi.candle_cache import CandleCache
        self.candle_cache = CandleCache()
        self._start_maintenance_thread()

        from iqoptionapi.trade_journal import TradeJournal
        self.trade_journal = TradeJournal(
            journal_dir=getattr(config, "JOURNAL_DIR", "./journal")
        )

        # --- Business Modules ---
        from iqoptionapi.circuit_breaker import CircuitBreaker
        self.circuit_breaker = CircuitBreaker(
            max_consecutive_losses=getattr(config, "CB_MAX_CONSECUTIVE_LOSSES", 3),
            max_session_loss_usd=getattr(config, "CB_MAX_SESSION_LOSS_USD", 10.0),
            max_drawdown_pct=getattr(config, "CB_MAX_DRAWDOWN_PCT", 0.10),
            recovery_wait_secs=getattr(config, "CB_RECOVERY_WAIT_SECS", 300.0)
        )

        from iqoptionapi.martingale_guard import MartingaleGuard, MoneyManagement
        mm_strat = MoneyManagement.FLAT
        try:
            mm_strat = MoneyManagement(getattr(config, "MM_DEFAULT_STRATEGY", "flat"))
        except: pass
        self.martingale_guard = MartingaleGuard(
            strategy=mm_strat,
            base_amount=getattr(config, "MM_BASE_AMOUNT", 1.0),
            max_steps=getattr(config, "MM_MAX_STEPS", 4),
            max_amount_usd=getattr(config, "MM_MAX_AMOUNT_USD", 50.0),
            max_balance_pct=getattr(config, "MM_MAX_BALANCE_PCT", 0.05)
        )

        from iqoptionapi.strategy.signal_consensus import SignalConsensus
        self.signal_consensus = SignalConsensus(strategies=[])

        from iqoptionapi.validator import Validator
        self.validator = Validator(config)

        from iqoptionapi.session_scheduler import SessionScheduler
        self.session_scheduler = SessionScheduler()

        # --- Modules depending on trade_journal ---
        from iqoptionapi.performance import PerformanceTracker
        self.performance = PerformanceTracker(self.trade_journal)
        
        from iqoptionapi.reconciler import Reconciler
        self._reconciler = Reconciler(self)

        # --- Intelligence Modules (depend on candle_cache) ---
        from iqoptionapi.strategy.market_quality import MarketQualityMonitor
        self.market_quality = MarketQualityMonitor(self.candle_cache)
        from iqoptionapi.strategy.pattern_engine import PatternEngine
        self.pattern_engine = PatternEngine(self.candle_cache)
        from iqoptionapi.strategy.market_regime import MarketRegime
        self.market_regime = MarketRegime(self.candle_cache)
        from iqoptionapi.strategy.correlation_engine import CorrelationEngine
        self.correlation_engine = CorrelationEngine(self.candle_cache)

        # --- Scanner (depends on modules above) ---
        from iqoptionapi.asset_scanner import AssetScanner
        self.asset_scanner = AssetScanner(self)

        # --- Subscription Manager (Sprint 3) ---
        from iqoptionapi.subscription_manager import SubscriptionManager
        self.subscription_manager = SubscriptionManager(self)

        self.size = [1, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800,
                     3600, 7200, 14400, 28800, 43200, 86400, 604800, 2592000]
        self.email = email
        self._credential_store = CredentialStore(email, password)
        self._reconnect_manager = ReconnectManager()
        self._idempotency = IdempotencyRegistry()
        self._order_bucket = TokenBucket(block=True)
        self.api_event_stores = {}
        self.suspend = 0.5
        self.thread = None
        self.subscribe_candle = []
        self.subscribe_candle_all_size = []
        self.subscribe_mood = []
        self.subscribe_indicators = []
        # for digit
        self.get_digital_spot_profit_after_sale_data = nested_dict(2, int)
        self.get_realtime_strike_list_temp_data = {}
        self.get_realtime_strike_list_temp_expiration = 0
        # Sprint 4 TAREA 4: Browser-compatible session headers
        self.SESSION_HEADER = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Referer": "https://iqoption.com/",
        }

        self.SESSION_COOKIE = {}
        # Sprint 5: State Synchronization
        self.positions_state_data = {}
        self.pending_orders_data = {}


    # --------------------------------------------------------------------------

    def get_server_timestamp(self):
        return self.api.timesync.server_timestamp

    def re_subscribe_stream(self):
        # SPRINT 4: Stealth re-subscription via SubscriptionManager
        if hasattr(self, 'subscription_manager'):
            # Batch subscribe all cached candles
            for ac in self.subscribe_candle:
                sp = ac.split(",")
                active = sp[0]
                size = int(sp[1])
                self.subscription_manager.subscribe_candle(active, size)
            
            for ac in self.subscribe_candle_all_size:
                # Assuming this also goes through manager
                self.start_candles_all_size_stream(ac)
            
            for ac in self.subscribe_mood:
                self.start_mood_stream(ac)
        else:
            # Fallback for older instances
            for ac in self.subscribe_candle:
                sp = ac.split(",")
                self.start_candles_one_stream(sp[0], sp[1])
            for ac in self.subscribe_candle_all_size:
                self.start_candles_all_size_stream(ac)
            for ac in self.subscribe_mood:
                self.start_mood_stream(ac)

    def set_session(self, header, cookie):
        self.SESSION_HEADER = header
        self.SESSION_COOKIE = cookie

    def close(self):
        """Gracefully close WebSocket and HTTP session."""
        self._stop_heartbeat_watchdog()
        try:
            self.api.close()
        except Exception:
            pass
        close_shared_session()
        get_logger(__name__).info("IQ_Option instance closed cleanly.")

    # ── Sprint 4 TAREA 2: Wait for initialization-data before returning True ──
    def _wait_for_init_data(self, *args, **kwargs):
        return super()._wait_for_init_data(*args, **kwargs)

    def connect(self, sms_code=None, ssid=None):
        if ssid:
            self.ssid = ssid

        if hasattr(self, 'api') and hasattr(self.api, 'websocket_client'):
            try:
                self.api.close()
            except Exception:
                pass

        self.api = IQOptionAPI(
            "ws.iqoption.com", self.email)
        
        if hasattr(self, 'ssid') and self.ssid:
            self.api.SSID = self.ssid
        
        # Initialize event stores required for non-blocking result waits (Sprint 1)
        self.api.socket_option_closed_event = defaultdict(threading.Event)
        self.api.result_event_store = defaultdict(threading.Event)
        self.api.position_changed_event_store = defaultdict(threading.Event)
        check = None

        # 2FA--
        if sms_code is not None:
            self.api.setTokenSMS(self.resp_sms)
            status, reason = self.api.connect2fa(sms_code)
            if not status:
                return status, reason
        # 2FA--

        self.api.set_session(headers=self.SESSION_HEADER,
                             cookies=self.SESSION_COOKIE)

        from iqoptionapi.ip_rotation import connect_with_rotation
        def _do_connect():
            return self.api.connect(self._credential_store.consume())

        check, reason = connect_with_rotation(
            _do_connect,
            max_attempts=3,
            rotate_on_fail=True
        )
        if check:
            # SPRINT 6: Store credentials for refresh worker
            self._credentials = (self.email, self._credential_store._password)
            
            # Register callbacks for resilience (S1-03)
            self.api._reconnect_callback = self._auto_reconnect
            self.api._heartbeat_callback = lambda: setattr(self, '_last_heartbeat', __import__('time').time())
            
            self._reconnect_manager.reset()
            self._idempotency.purge_expired()

        if check == True:
            # Sprint 6: Stealth mode post-auth delay
            import random
            time.sleep(random.uniform(config.STEALTH_POST_AUTH_DELAY * 0.8, config.STEALTH_POST_AUTH_DELAY * 1.2))
            
            # Clear instruments cache to prevent stale data from prior sessions
            if hasattr(self.api, '_instruments_by_category'):
                self.api._instruments_by_category.clear()
            self.api.instruments = {"instruments": []}

            # -------------reconnect subscribe_candle
            self.re_subscribe_stream()

            # ---------for async get name: "position-changed", microserviceName
            if self.api.balance_id == None:
                self.api.balance_id_event.wait(timeout=10)

            self.position_change_all(
                "subscribeMessage", self.api.balance_id)

            self.order_changed_all("subscribeMessage")
            self.api.setOptions(1, True)


            # Auto-update asset catalogs on successful connection
            try:
                self.update_ACTIVES_OPCODE()
                get_logger(__name__).info("Live Asset Catalogs (Binary, Crypto, Forex, CFD) successfully synchronized.")
            except Exception as e:
                get_logger(__name__).warning("Failed to auto-update asset catalogs: %s", e)

            # Sprint 4 TAREA 2: Wait for initialization-data before exposing connection
            init_ready = self._wait_for_init_data(timeout=25.0)
            if not init_ready:
                get_logger(__name__).warning(
                    "connect(): initialization-data no llegó en 25s. "
                    "get_all_open_time() puede retornar listas vacías."
                )

            self._start_heartbeat_watchdog()
            
            # Sprint 5: State Synchronization
            self.sync_state_on_connect()
            
            # Sprint 6: Token Refresh Worker
            if getattr(config, "AUTO_REFRESH_TOKEN", True):
                self._start_token_refresh_worker()
            
            return True, None
        else:
            try:
                reason_dict = json.loads(reason)
                if reason_dict.get('code') == 'verify':
                    response = self.api.send_sms_code(reason_dict['token'])

                    if response.json()['code'] != 'success':
                        return False, response.json()['message']

                    # token_sms
                    self.resp_sms = response
                    return False, "2FA"
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
            return False, reason

    # self.update_ACTIVES_OPCODE()

    def connect_2fa(self, sms_code):
        return self.connect(sms_code=sms_code)

    def _auto_reconnect(self, *args, **kwargs):
        return super()._auto_reconnect(*args, **kwargs)

    def _start_heartbeat_watchdog(self, *args, **kwargs):
        return super()._start_heartbeat_watchdog(*args, **kwargs)

    def _stop_heartbeat_watchdog(self, *args, **kwargs):
        return super()._stop_heartbeat_watchdog(*args, **kwargs)

    def check_connect(self, *args, **kwargs):
        return super().check_connect(*args, **kwargs)
        # wait for timestamp getting

    # _________________________UPDATE ACTIVES OPCODE_____________________
    def get_all_ACTIVES_OPCODE(self):
        return OP_code.ACTIVES

    def update_ACTIVES_OPCODE(self):
        # update from binary option
        self.get_ALL_Binary_ACTIVES_OPCODE()
        # crypto /dorex/cfd
        self.instruments_input_all_in_ACTIVES()
        dicc = {}
        for lis in sorted(OP_code.ACTIVES.items(), key=operator.itemgetter(1)):
            dicc[lis[0]] = lis[1]
        OP_code.ACTIVES = dicc

    def get_name_by_activeId(self, activeId):
        info = self.get_financial_information(activeId)
        try:
            return info["msg"]["data"]["active"]["name"]
        except Exception as e:
            return None

    def get_financial_information(self, activeId):
        self.api.financial_information = None
        if hasattr(self.api, 'financial_information_event'):
            self.api.financial_information_event.clear()
        self.api.get_financial_information(activeId)
        
        if hasattr(self.api, 'financial_information_event'):
            is_ready = self.api.financial_information_event.wait(timeout=30)
            if not is_ready:
                get_logger(__name__).error("Timeout waiting for financial information.")
                return None
        return self.api.financial_information

    def get_leader_board(self, country, from_position, to_position, near_traders_count, user_country_id=0, near_traders_country_count=0, top_country_count=0, top_count=0, top_type=2):
        self.api.leaderboard_deals_client = None

        country_id = Country.ID[country]
        self.api.leaderboard_deals_client_event.clear()
        self.api.Get_Leader_Board(country_id, user_country_id, from_position, to_position,
                                  near_traders_country_count, near_traders_count, top_country_count, top_count, top_type)

        is_ready = self.api.leaderboard_deals_client_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for leaderboard_deals_client')
        return self.api.leaderboard_deals_client

    def get_instruments(self, type):
        """
        Obtiene instrumentos por tipo ("crypto"/"forex"/"cfd").
        Intenta WS primero; si retorna lista vacía, hace fallback
        a extracción desde initialization-data (transparente).
        """
        time.sleep(self.suspend)
        self.api.instruments = None

        try:
            if hasattr(self.api, 'instruments_event'):
                self.api.instruments_event.clear()

            self.api.get_instruments(type)

            if hasattr(self.api, 'instruments_event'):
                is_ready = self.api.instruments_event.wait(timeout=10)
                if not is_ready:
                    get_logger(__name__).warning(
                        "WS timeout for instruments type: %s", type)
        except Exception as e:
            get_logger(__name__).error(
                'get_instruments WS error for type=%s: %s', type, e)

        ws_result = getattr(self.api, 'instruments', {"instruments": []})
        ws_instruments = []
        if isinstance(ws_result, dict):
            ws_instruments = ws_result.get("instruments", [])

        # ── FALLBACK: init-data extraction when WS returns empty ──
        if not ws_instruments:
            get_logger(__name__).info(
                "WS returned empty for type=%s, attempting init-data fallback", type)
            try:
                from iqoptionapi.http.instruments import _extract_instruments_from_init
                # Use CACHED init data (already populated during connect())
                # Priority: init_v2 (modern) > init_v1 (classic)
                init_data = getattr(self.api, 'api_option_init_all_result_v2', None)
                if init_data and isinstance(init_data, dict):
                    instruments = _extract_instruments_from_init(init_data, type)
                    if instruments:
                        get_logger(__name__).info(
                            "Init-data fallback (v2 cache): %d instruments for type=%s",
                            len(instruments), type)
                        return {"instruments": instruments}

                # Try classic init cache
                init_data_v1 = getattr(self.api, 'api_option_init_all_result', None)
                if init_data_v1 and isinstance(init_data_v1, dict):
                    result_data = init_data_v1.get("result", init_data_v1)
                    instruments = _extract_instruments_from_init(result_data, type)
                    if instruments:
                        get_logger(__name__).info(
                            "Init-data fallback (v1 cache): %d instruments for type=%s",
                            len(instruments), type)
                        return {"instruments": instruments}

                # Last resort: fetch fresh init data
                get_logger(__name__).info(
                    "No cached init data, fetching fresh for type=%s", type)
                fresh_init = self.get_all_init_v2()
                if fresh_init and isinstance(fresh_init, dict):
                    instruments = _extract_instruments_from_init(fresh_init, type)
                    if instruments:
                        get_logger(__name__).info(
                            "Init-data fallback (fresh): %d instruments for type=%s",
                            len(instruments), type)
                        return {"instruments": instruments}

            except Exception as e:
                get_logger(__name__).error(
                    "Init-data fallback failed for type=%s: %s", type, e)

        return ws_result if ws_instruments else {"instruments": []}

    def instruments_input_to_ACTIVES(self, type):
        instruments = self.get_instruments(type)
        if instruments and isinstance(instruments, dict) and "instruments" in instruments:
            for ins in instruments["instruments"]:
                OP_code.ACTIVES[ins["id"]] = ins["active_id"]

    def instruments_input_all_in_ACTIVES(self):
        self.instruments_input_to_ACTIVES("crypto")
        self.instruments_input_to_ACTIVES("forex")
        self.instruments_input_to_ACTIVES("cfd")

    def get_ALL_Binary_ACTIVES_OPCODE(self):
        init_info = self.get_all_init_v2()
        if not init_info or not isinstance(init_info, dict):
            return

        for dirr in (["binary", "turbo", "blitz"]):
            if dirr in init_info:
                for i in init_info[dirr]["actives"]:
                    OP_code.ACTIVES[(init_info[dirr]
                                     ["actives"][i]["name"]).split(".")[1]] = int(i)

    # _________________________self.api.get_api_option_init_all() wss______________
    def get_all_init(self):
        """Solicita initialization-data. Una sola llamada WS por sesión."""
        if self.api.api_option_init_all_result is not None:
            return self.api.api_option_init_all_result
            
        self.api.api_option_init_all_result_event.clear()
        self.api.get_api_option_init_all()
        is_ready = self.api.api_option_init_all_result_event.wait(timeout=config.TIMEOUT_ALL_INIT)
        
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for get_all_init")
            
        return self.api.api_option_init_all_result

    def get_all_init_v2(self):
        """Solicita initialization-data v2. Una sola llamada WS por sesión."""
        if self.api.api_option_init_all_result_v2 is not None:
            return self.api.api_option_init_all_result_v2
            
        if self.check_connect() == False:
            self.connect()
            
        self.api.api_option_init_all_result_v2_event.clear()
        self.api.get_api_option_init_all_v2()
        is_ready = self.api.api_option_init_all_result_v2_event.wait(timeout=config.TIMEOUT_ALL_INIT)
        
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for get_all_init_v2")
            
        return self.api.api_option_init_all_result_v2

    # ------- chek if binary/digit/cfd/stock... if open or not

    def __get_binary_open(self):
        # for turbo and binary pairs
        # SPRINT 13: Intentar v1 y v2 para maxima compatibilidad
        v2_data = self.get_all_init_v2()
        v1_data = self.get_all_init()
        
        binary_list = ["binary", "turbo", "blitz"]
        
        # Procesar v2 (initialization-data)
        if v2_data:
            for option in binary_list:
                if option in v2_data:
                    for actives_id in v2_data[option]["actives"]:
                        active = v2_data[option]["actives"][actives_id]
                        name = str(active["name"]).split(".")[1]
                        self.OPEN_TIME[option][name]["open"] = active["enabled"] and not active.get("is_suspended", False)
        
        # Procesar v1 (api_option_init_all_result) como fallback/complemento
        if v1_data and v1_data.get("result"):
            res = v1_data["result"]
            for option in binary_list:
                if option in res:
                    for actives_id in res[option]["actives"]:
                        active = res[option]["actives"][actives_id]
                        name = str(active["name"]).split(".")[1]
                        # Solo sobreescribir si no estaba abierto en v2 (v1 suele ser mas confiable para Binary)
                        self.OPEN_TIME[option][name]["open"] = active["enabled"] and not active.get("is_suspended", False)

    def __get_digital_open(self):
        # for digital options
        digital_data = []
        for _ in range(3):
            data = self.get_digital_underlying_list_data()
            if isinstance(data, dict) and "underlying" in data:
                digital_data = data.get("underlying", [])
            elif isinstance(data, list):
                digital_data = data
            
            get_logger(__name__).debug("__get_digital_open: data=%s", digital_data)
            if digital_data:
                break
            time.sleep(2)
            
        for digital in digital_data:
            name = digital.get("underlying")
            if not name:
                continue
            schedule = digital.get("schedule", [])
            self.OPEN_TIME["digital"][name]["open"] = False
            for schedule_time in schedule:
                start = schedule_time.get("open", 0)
                end = schedule_time.get("close", 0)
                if start < time.time() < end:
                    self.OPEN_TIME["digital"][name]["open"] = True

        if not digital_data:
            try:
                insts = self.get_instruments("digital-option")
                if insts and "instruments" in insts:
                    for detail in insts["instruments"]:
                        n = detail.get("name")
                        if not n: continue
                        if "." in n:
                            n = n.split(".")[1]
                        self.OPEN_TIME["digital"][n]["open"] = any(s.get("open", 0) < time.time() < s.get("close", 0) for s in detail.get("schedule", []))
            except Exception:
                pass

        # ULTIMATE FALLBACK: Mirror binary/turbo assets if digital list is still empty (Sprint 4 Validation fix)
        if not any(v.get("open") for v in self.OPEN_TIME["digital"].values()):
            get_logger(__name__).info("Digital discovery failed, mirroring binary/turbo asset availability")
            for cat in ["binary", "turbo"]:
                for asset, info in self.OPEN_TIME.get(cat, {}).items():
                    if info.get("open"):
                        self.OPEN_TIME["digital"][asset]["open"] = True

    def __get_other_open(self):
        # Crypto and etc pairs
        instrument_list = ["cfd", "forex", "crypto", "stocks", "commodities", "indices", "etf"]
        for instruments_type in instrument_list:
            # Sprint 6: Stealth mode delay
            if instruments_type != instrument_list[0]:
                import random
                time.sleep(random.uniform(config.STEALTH_INSTRUMENT_REQUEST_DELAY * 0.8, config.STEALTH_INSTRUMENT_REQUEST_DELAY * 1.2))

            ins_data = []
            for _ in range(3):
                result = self.get_instruments(instruments_type)
                if isinstance(result, dict) and "instruments" in result:
                    ins_data = result.get("instruments", [])
                elif isinstance(result, list):
                    ins_data = result
                elif hasattr(result, "get"):
                    ins_data = result.get("instruments", [])
                
                if ins_data:
                    break
                time.sleep(2)
                
            for detail in ins_data:
                name = detail.get("name")
                if not name:
                    continue
                if "." in name:
                    name = name.split(".")[1]
                schedule = detail.get("schedule", [])
                self.OPEN_TIME[instruments_type][name]["open"] = False
                for schedule_time in schedule:
                    start = schedule_time.get("open", 0)
                    end = schedule_time.get("close", 0)
                    if start < time.time() < end:
                        self.OPEN_TIME[instruments_type][name]["open"] = True

    def get_all_open_time(self):
        # all pairs openned
        self.OPEN_TIME = nested_dict(3, dict)
        binary = threading.Thread(target=self.__get_binary_open)
        digital = threading.Thread(target=self.__get_digital_open)
        other = threading.Thread(target=self.__get_other_open)

        binary.start(), digital.start(), other.start()

        binary.join(), digital.join(), other.join()
        return self.OPEN_TIME

    def get_blitz_instruments(self):
        """
        Returns the catalog of Blitz instruments extracted from the
        initialization-data WebSocket message. Structure:
        { "ASSET_NAME": { "id": int, "ticker": str, "enabled": bool,
                          "is_suspended": bool, "open": bool,
                          "expirations": [30, 45, ...] } }

        Blitz instruments are NOT available via get_instruments() —
        the server rejects type="blitz" with error 4000.
        """
        blitz = getattr(self.api, 'blitz_instruments', {})
        if not blitz:
            # Force refresh from server — initialization-data handler
            # will populate api.blitz_instruments as a side effect
            self.get_all_init_v2()
            blitz = getattr(self.api, 'blitz_instruments', {})
        return blitz

    # --------for binary option detail

    def get_binary_option_detail(self):
        detail = nested_dict(2, dict)
        init_info = self.get_all_init()
        for actives in init_info["result"]["turbo"]["actives"]:
            name = init_info["result"]["turbo"]["actives"][actives]["name"]
            name = name[name.index(".") + 1:len(name)]
            detail[name]["turbo"] = init_info["result"]["turbo"]["actives"][actives]

        for actives in init_info["result"]["binary"]["actives"]:
            name = init_info["result"]["binary"]["actives"][actives]["name"]
            name = name[name.index(".") + 1:len(name)]
            detail[name]["binary"] = init_info["result"]["binary"]["actives"][actives]
        return detail

    def get_all_profit(self):
        all_profit = nested_dict(2, dict)
        init_info = self.get_all_init()
        for actives in init_info["result"]["turbo"]["actives"]:
            name = init_info["result"]["turbo"]["actives"][actives]["name"]
            name = name[name.index(".") + 1:len(name)]
            all_profit[name]["turbo"] = (
                100.0 -
                init_info["result"]["turbo"]["actives"][actives]["option"]["profit"][
                    "commission"]) / 100.0

        for actives in init_info["result"]["binary"]["actives"]:
            name = init_info["result"]["binary"]["actives"][actives]["name"]
            name = name[name.index(".") + 1:len(name)]
            all_profit[name]["binary"] = (
                100.0 -
                init_info["result"]["binary"]["actives"][actives]["option"]["profit"][
                    "commission"]) / 100.0
        return all_profit

    # ----------------------------------------

    # ______________________________________self.api.getprofile() https________________________________

    def get_profile_ansyc(self):
        resp = self.api.getprofile()
        if resp and resp.status_code == 200:
            data = resp.json()
            # Si viene envuelto en result (HTTP), lo desempaquetamos
            if isinstance(data, dict) and data.get("isSuccessful"):
                p_msg = data.get("result")
            else:
                p_msg = data
            
            # SPRINT 13: Validacion de integridad. Si no hay balances, ignorar HTTP (posible block/limit)
            if p_msg and "balances" in p_msg and p_msg["balances"]:
                self.api.profile.msg = p_msg
                if hasattr(self.api, 'profile_msg_event'):
                    self.api.profile_msg_event.set()
        
        if self.api.profile.msg is None or "balances" not in self.api.profile.msg:
            # Fallback a esperar mensaje WS
            get_logger(__name__).info("HTTP profile missing balances, waiting for WS profile...")
            is_ready = self.api.profile_msg_event.wait(timeout=config.TIMEOUT_WS_DATA)
            if not is_ready:
                get_logger(__name__).warning("Timeout waiting for profile via WS")
        
        return self.api.profile.msg


    def get_currency(self):
        balances_raw = self.get_balances()
        if balances_raw and "msg" in balances_raw:
            for balance in balances_raw["msg"]:
                if balance["id"] == self.api.balance_id:
                    return balance["currency"]
        return None

    def get_balance_id(self):
        return self.api.balance_id


    def get_balance(self):

        balances_raw = self.get_balances()
        if balances_raw and "msg" in balances_raw:
            for balance in balances_raw["msg"]:
                if balance["id"] == self.api.balance_id:
                    return balance["amount"]
        return 0

    def get_balances(self):
        self.api.balances_raw = None
        if hasattr(self.api, 'balances_raw_event'):
            self.api.balances_raw_event.clear()
        self.api.get_balances()
        
        if hasattr(self.api, 'balances_raw_event'):
            is_ready = self.api.balances_raw_event.wait(timeout=30)
            if not is_ready:
                get_logger(__name__).error("Timeout waiting for balances_raw.")
                return None
        return self.api.balances_raw.get("msg", []) if self.api.balances_raw else []

    def get_balance_mode(self):
        # self.api.profile.balance_type=None
        profile = self.get_profile_ansyc()
        for balance in profile.get("balances"):
            if balance["id"] == self.api.balance_id:
                if balance["type"] == 1:
                    return "REAL"
                elif balance["type"] == 4:
                    return "PRACTICE"

                elif balance["type"] == 2:
                    return "TOURNAMENT"

    def reset_practice_balance(self, *args, **kwargs):
        return super().reset_practice_balance(*args, **kwargs)

    def position_change_all(self, Main_Name, user_balance_id):
        instrument_type = ["cfd", "forex", "crypto",
                           "digital-option", "turbo-option", "binary-option"]
        for ins in instrument_type:
            self.api.portfolio(Main_Name=Main_Name, name="portfolio.position-changed",
                               instrument_type=ins, user_balance_id=user_balance_id)

    def order_changed_all(self, Main_Name):
        instrument_type = ["cfd", "forex", "crypto",
                           "digital-option", "turbo-option", "binary-option"]
        for ins in instrument_type:
            self.api.portfolio(
                Main_Name=Main_Name, name="portfolio.order-changed", instrument_type=ins)

    def change_balance(self, *args, **kwargs):
        return super().change_balance(*args, **kwargs)

    # ________________________________________________________________________
    # _______________________        CANDLE      _____________________________
    # ________________________self.api.getcandles() wss________________________

    def get_candles(self, *args, **kwargs):
        return super().get_candles(*args, **kwargs)

    #######################################################
    # ______________________________________________________
    # _____________________REAL TIME CANDLE_________________
    # ______________________________________________________
    #######################################################

    def stop_candles_stream(self, ACTIVE, size):
        if size == "all":
            self.stop_candles_all_size_stream(ACTIVE)
        elif size in self.size:
            self.stop_candles_one_stream(ACTIVE, size)
        else:
            get_logger(__name__).error(
                '**error** start_candles_stream please input right size')

    def get_realtime_candles(self, *args, **kwargs):
        return super().get_realtime_candles(*args, **kwargs)

    def get_all_realtime_candles(self):
        return self.api.real_time_candles

    ################################################
    # ---------REAL TIME CANDLE Subset Function---------
    ################################################
    # ---------------------full dict get_candle-----------------------

    def full_realtime_get_candle(self, ACTIVE, size, maxdict):
        candles = self.get_candles(
            ACTIVE, size, maxdict, self.api.timesync.server_timestamp)
        for can in candles:
            self.api.real_time_candles[str(
                ACTIVE)][int(size)][can["from"]] = can

    # ------------------------Subscribe ONE SIZE-----------------------


    # ------------------------Subscribe ALL SIZE-----------------------



    # ------------------------top_assets_updated---------------------------------------------

    def subscribe_top_assets_updated(self, instrument_type):
        self.api.Subscribe_Top_Assets_Updated(instrument_type)

    def unsubscribe_top_assets_updated(self, instrument_type):
        self.api.Unsubscribe_Top_Assets_Updated(instrument_type)

    def get_top_assets_updated(self, instrument_type):
        if instrument_type in self.api.top_assets_updated_data:
            return self.api.top_assets_updated_data[instrument_type]
        else:
            return None

    # ----------------- Real-time Instruments (Sprint 3) -----------------
    def subscribe_instruments_realtime(self, instrument_type):
        """
        Suscribe a la lista de instrumentos en tiempo real para detectar aperturas/cierres.
        """
        self.subscription_manager.subscribe_instruments_realtime(instrument_type)

    def unsubscribe_instruments_realtime(self, instrument_type):
        """
        Desuscribe de instrumentos en tiempo real.
        """
        self.api.unsubscribe_instruments_list(instrument_type)

    # ------------------------commission_________
    # instrument_type: "binary-option"/"turbo-option"/"digital-option"/"crypto"/"forex"/"cfd"
    def subscribe_commission_changed(self, instrument_type):

        self.api.Subscribe_Commission_Changed(instrument_type)

    def unsubscribe_commission_changed(self, instrument_type):
        self.api.Unsubscribe_Commission_Changed(instrument_type)

    def get_commission_change(self, instrument_type):
        return self.api.subscribe_commission_changed_data[instrument_type]

    # -----------------------------------------------

    # -----------------traders_mood----------------------


    def stop_mood_stream(self, ACTIVES, instrument="turbo-option"):
        if ACTIVES in self.subscribe_mood:
            del self.subscribe_mood[ACTIVES]
        self.api.unsubscribe_Traders_mood(OP_code.ACTIVES[ACTIVES], instrument)

    def get_traders_mood(self, ACTIVES):
        # return highter %
        return self.api.traders_mood[OP_code.ACTIVES[ACTIVES]]

    def get_all_traders_mood(self):
        # return highter %
        return self.api.traders_mood

##############################################################################################

    # -----------------technical_indicators----------------------

    def get_technical_indicators(self, ACTIVES):
        self.api.technical_indicators[str(ACTIVES)] = None
        self.api.technical_indicators_event.clear()
        self.api.get_technical_indicators(OP_code.ACTIVES[ACTIVES])
        is_ready = self.api.technical_indicators_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for technical_indicators: %s", ACTIVES)
        return self.api.technical_indicators.get(str(ACTIVES))

##############################################################################################

    # ── Non-blocking Result Helper ────────────────────────────
    def _wait_result(
        self,
        order_id: int | str,
        result_store,
        event_store: dict,
        timeout: float = 120.0,
    ) -> dict | None:
        """Espera el resultado de un trade sin bloquear el thread forever.
        
        Retorna el dict del resultado, o None si vence el timeout.
        """
        try:
            start_wait = time.time()
            get_logger(__name__).debug("_wait_result: waiting for order_id=%s store=%s", order_id, type(event_store).__name__)
            
            # S7: Asegurar que el ID sea int para coincidir con las llaves del event_store (defaultdict)
            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                pass

            # S7: Manejar tanto dicts/defaultdicts de eventos como eventos únicos (legacy)
            if hasattr(event_store, "wait"):
                event = event_store
            elif hasattr(event_store, "get"):
                event = event_store.get(order_id)
                if not hasattr(event, "wait"):
                    event = threading.Event()
                    try:
                        event_store[order_id] = event
                    except (TypeError, AttributeError):
                        pass
            else:
                try:
                    event = event_store[order_id]
                except (TypeError, KeyError):
                    event = threading.Event()

            fired = event.wait(timeout=timeout)
            elapsed = time.time() - start_wait
            
            if not fired:
                get_logger(__name__).debug("_wait_result: timeout for order_id=%s after %.2fs", order_id, elapsed)
                return None
            
            # Si el result_store tiene un método get_id_data (como listinfodata)
            if hasattr(result_store, "get_id_data"):
                res = result_store.get_id_data(order_id)
            elif hasattr(result_store, "get"):
                # S7: Intentar obtener del store con el ID procesado
                res = result_store.get(order_id) if result_store is not None else None
            else:
                try:
                    res = result_store[order_id] if result_store is not None else None
                except (TypeError, KeyError):
                    res = None
            
            # Fallback para Digital/CFD: si res es None y es un check_win que usa order_async
            if res is None and hasattr(self, "get_async_order"):
                async_data = self.get_async_order(order_id)
                # Retornar el primer mensaje disponible (ej: position-changed)
                for k in ["position-changed", "option-closed", "option"]:
                    if k in async_data:
                        res = async_data.get(k)
                        break
            
            get_logger(__name__).debug("_wait_result: result=%s elapsed=%.2fs", res, elapsed)
            return res

        except Exception as e:
            get_logger(__name__).warning("_wait_result error for order_id=%s: %s", order_id, e)
            return None
        finally:
            # S1-T6: Cleanup event store to prevent memory leaks (Garantizado via finally)
            if not hasattr(event_store, "wait"):
                try:
                    del event_store[order_id]
                except (KeyError, UnboundLocalError, TypeError):
                    pass


##############################################################################################

    def check_binary_order(self, *args, **kwargs):
        return super().check_binary_order(*args, **kwargs)

    def check_win(self, *args, **kwargs):
        return super().check_win(*args, **kwargs)

    def check_win_v2(self, *args, **kwargs):
        return super().check_win_v2(*args, **kwargs)

    def check_win_v4(self, *args, **kwargs):
        return super().check_win_v4(*args, **kwargs)

    def check_win_v3(self, *args, **kwargs):
        return super().check_win_v3(*args, **kwargs)

    # -------------------get infomation only for binary option------------------------

    def get_betinfo(self, *args, **kwargs):
        return super().get_betinfo(*args, **kwargs)

    def get_optioninfo(self, *args, **kwargs):
        return super().get_optioninfo(*args, **kwargs)

    def get_optioninfo_v2(self, *args, **kwargs):
        return super().get_optioninfo_v2(*args, **kwargs)

    # __________________________BUY__________________________

    # __________________FOR OPTION____________________________

    def buy(self, *args, **kwargs):
        try:
            if hasattr(self, "_order_bucket"):
                self._order_bucket.consume()
            return super().buy(*args, **kwargs)
        except RateLimitExceededError:
            return False, None

    def buy_multi(self, *args, **kwargs):
        try:
            if hasattr(self, "_order_bucket"):
                self._order_bucket.consume()
            return super().buy_multi(*args, **kwargs)
        except RateLimitExceededError:
            return False, None

    def get_remaning(self, duration):
        for remaning in get_remaning_time(self.api.timesync.server_timestamp):
            if remaning[0] == duration:
                return remaning[1]
        get_logger(__name__).error('get_remaning(self,duration) ERROR duration')
        return "ERROR duration"

    def buy_by_raw_expirations(self, *args, **kwargs):
        return super().buy_by_raw_expirations(*args, **kwargs)
    def sell_option(self, *args, **kwargs):
        try:
            if hasattr(self, "_order_bucket"):
                self._order_bucket.consume()
            return super().sell_option(*args, **kwargs)
        except RateLimitExceededError:
            return None

    def sell_digital_option(self, *args, **kwargs):
        try:
            if hasattr(self, "_order_bucket"):
                self._order_bucket.consume()
            return super().sell_digital_option(*args, **kwargs)
        except RateLimitExceededError:
            return None
    def buy_digital_spot(self, *args, **kwargs):
        try:
            if hasattr(self, "_order_bucket"):
                self._order_bucket.consume()
            return super().buy_digital_spot(*args, **kwargs)
        except RateLimitExceededError:
            return False, None

    def buy_digital_spot_v2(self, *args, **kwargs):
        try:
            if hasattr(self, "_order_bucket"):
                self._order_bucket.consume()
            return super().buy_digital_spot_v2(*args, **kwargs)
        except RateLimitExceededError:
            return False, None

    def get_digital_underlying_list_data(self):
        self.api.underlying_list_data = None
        self.api.get_digital_underlying()
        is_ready = self.api.underlying_list_data_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for underlying_list_data")
        return self.api.underlying_list_data

    def get_strike_list(self, ACTIVES, duration):
        self.api.strike_list_event.clear()
        self.api.get_strike_list(ACTIVES, duration)
        is_ready = self.api.strike_list_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for strike_list')
            return None, None
        
        ans = {}
        try:
            for data in self.api.strike_list["msg"]["strike"]:
                temp = {}
                temp["call"] = data["call"]["id"]
                temp["put"] = data["put"]["id"]
                ans[("%.6f" % (float(data["value"]) * 10e-7))] = temp
        except (KeyError, TypeError) as e:
            get_logger(__name__).error('**error** get_strike_list read problem: %s', e)
            return self.api.strike_list, None
        return self.api.strike_list, ans

    def subscribe_strike_list(self, *args, **kwargs):
        return super().subscribe_strike_list(*args, **kwargs)

    def unsubscribe_strike_list(self, *args, **kwargs):
        return super().unsubscribe_strike_list(*args, **kwargs)

    def get_instrument_quotes_generated_data(self, ACTIVE, duration):
        start_t = time.time()
        while self.api.instrument_quotes_generated_raw_data[ACTIVE][duration * 60] == {} and (time.time() - start_t < 15.0):
            self.api.instrument_quotes_generated_event.wait(timeout=1)
            self.api.instrument_quotes_generated_event.clear()
        return self.api.instrument_quotes_generated_raw_data[ACTIVE][duration * 60]

    def get_realtime_strike_list(self, ACTIVE, duration):
        start_t = time.time()
        while not self.api.instrument_quotes_generated_data[ACTIVE][duration * 60] and (time.time() - start_t < 15.0):
            self.api.instrument_quotes_generated_event.wait(timeout=1)
            self.api.instrument_quotes_generated_event.clear()

        ans = {}
        now_timestamp = self.api.instrument_quotes_generated_timestamp[ACTIVE][duration * 60]

        while ans == {}:
            if self.get_realtime_strike_list_temp_data == {} or now_timestamp != self.get_realtime_strike_list_temp_expiration:
                raw_data, strike_list = self.get_strike_list(ACTIVE, duration)
                if raw_data:
                    self.get_realtime_strike_list_temp_expiration = raw_data["msg"]["expiration"]
                    self.get_realtime_strike_list_temp_data = strike_list
                else:
                    break
            else:
                strike_list = self.get_realtime_strike_list_temp_data

            profit = self.api.instrument_quotes_generated_data[ACTIVE][duration * 60]
            for price_key in strike_list:
                try:
                    side_data = {}
                    for side_key in strike_list[price_key]:
                        detail_data = {}
                        profit_d = profit[strike_list[price_key][side_key]]
                        detail_data["profit"] = profit_d
                        detail_data["id"] = strike_list[price_key][side_key]
                        side_data[side_key] = detail_data
                    ans[price_key] = side_data
                except (KeyError, TypeError) as e:
                    get_logger(__name__).error("Data extraction error: %s", e)
            
            if ans == {}:
                self.api.instrument_quotes_generated_event.wait(timeout=1)
                self.api.instrument_quotes_generated_event.clear()

        return ans

    def get_digital_current_profit(self, ACTIVE, duration):
        profit = self.api.instrument_quotes_generated_data[ACTIVE][duration * 60]
        for key in profit:
            if key.find("SPT") != -1:
                return profit[key]
        return False

    
    @rate_limited("_order_bucket")

    def get_digital_spot_profit_after_sale(self, position_id):
        def get_instrument_id_to_bid(data, instrument_id):
            for row in data["msg"]["quotes"]:
                if row["symbols"][0] == instrument_id:
                    return row["price"]["bid"]
            return None

        start_t = time.time()
        while self.get_async_order(position_id).get("position-changed") == {} and (time.time() - start_t < 15.0):
            self.api.position_changed_event.wait(timeout=1)
            self.api.position_changed_event.clear()
        # ___________________/*position*/_________________
        position = self.get_async_order(position_id)["position-changed"]["msg"]
        # doEURUSD201911040628PT1MPSPT
        # z mean check if call or not
        if "MPSPT" in position["instrument_id"]:
            z = False
        elif "MCSPT" in position["instrument_id"]:
            z = True
        else:
            get_logger(__name__).error(
                'get_digital_spot_profit_after_sale position error' + str(position["instrument_id"]))

        ACTIVES = position['raw_event']['instrument_underlying']
        amount = max(position['raw_event']["buy_amount"],
                     position['raw_event']["sell_amount"])
        start_duration = position["instrument_id"].find("PT") + 2
        end_duration = start_duration + \
            position["instrument_id"][start_duration:].find("M")

        duration = int(position["instrument_id"][start_duration:end_duration])
        z2 = False

        getAbsCount = position['raw_event']["count"]
        instrumentStrikeValue = position['raw_event']["instrument_strike_value"] / 1000000.0
        spotLowerInstrumentStrike = position['raw_event']["extra_data"]["lower_instrument_strike"] / 1000000.0
        spotUpperInstrumentStrike = position['raw_event']["extra_data"]["upper_instrument_strike"] / 1000000.0

        aVar = position['raw_event']["extra_data"]["lower_instrument_id"]
        aVar2 = position['raw_event']["extra_data"]["upper_instrument_id"]
        getRate = position['raw_event']["currency_rate"]

        # ___________________/*position*/_________________
        instrument_quotes_generated_data = self.get_instrument_quotes_generated_data(
            ACTIVES, duration)


        f_tmp = get_instrument_id_to_bid(
            instrument_quotes_generated_data, aVar)
        # f is bidprice of lower_instrument_id ,f2 is bidprice of upper_instrument_id
        if f_tmp != None:
            self.get_digital_spot_profit_after_sale_data[position_id]["f"] = f_tmp
            f = f_tmp
        else:
            f = self.get_digital_spot_profit_after_sale_data[position_id]["f"]

        f2_tmp = get_instrument_id_to_bid(
            instrument_quotes_generated_data, aVar2)
        if f2_tmp != None:
            self.get_digital_spot_profit_after_sale_data[position_id]["f2"] = f2_tmp
            f2 = f2_tmp
        else:
            f2 = self.get_digital_spot_profit_after_sale_data[position_id]["f2"]

        if (spotLowerInstrumentStrike != instrumentStrikeValue) and f != None and f2 != None:

            if (spotLowerInstrumentStrike > instrumentStrikeValue or instrumentStrikeValue > spotUpperInstrumentStrike):
                if z:
                    instrumentStrikeValue = (spotUpperInstrumentStrike - instrumentStrikeValue) / abs(
                        spotUpperInstrumentStrike - spotLowerInstrumentStrike)
                    f = abs(f2 - f)
                else:
                    instrumentStrikeValue = (instrumentStrikeValue - spotUpperInstrumentStrike) / abs(
                        spotUpperInstrumentStrike - spotLowerInstrumentStrike)
                    f = abs(f2 - f)

            elif z:
                f += ((instrumentStrikeValue - spotLowerInstrumentStrike) /
                      (spotUpperInstrumentStrike - spotLowerInstrumentStrike)) * (f2 - f)
            else:
                instrumentStrikeValue = (spotUpperInstrumentStrike - instrumentStrikeValue) / (
                    spotUpperInstrumentStrike - spotLowerInstrumentStrike)
                f -= f2
            f = f2 + (instrumentStrikeValue * f)

        if z2:
            pass
        if f != None:
            # price=f/getRate
            price = (f / getRate)
            # getAbsCount Reference
            return price * getAbsCount - amount
        else:
            return None


    @rate_limited("_order_bucket")
    def close_digital_option(self, position_id):
        # Wait for position info
        while self.get_async_order(position_id).get("position-changed") == {}:
            is_ready = self.api.position_changed_event.wait(timeout=config.TIMEOUT_WS_DATA)
            if not is_ready:
                get_logger(__name__).warning("Timeout waiting for position_changed in close_digital_option")
                break
            self.api.position_changed_event.clear()
        position_changed = self.get_async_order(position_id)["position-changed"]["msg"]
        
        self.api.result_event.clear()
        self.api.close_digital_option(position_changed["external_id"])
        is_ready = self.api.result_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for close_digital_option result')
        return self.api.result

    def check_win_digital(self, *args, **kwargs):
        return super().check_win_digital(*args, **kwargs)


    def check_win_digital_v2(self, *args, **kwargs):
        return super().check_win_digital_v2(*args, **kwargs)

    # ----------------------------------------------------------
    # -----------------BUY_for__Forex__&&__stock(cfd)__&&__ctrpto

    # ── Blitz / Pending Order Protocol (Sprint 3) ────────────────


    def cancel_pending_order(self, *args, **kwargs):
        return super().cancel_pending_order(*args, **kwargs)

    def get_pending_orders(self, *args, **kwargs):
        return super().get_pending_orders(*args, **kwargs)

    def get_marginal_balance(self, instrument_type):
        """
        Obtiene el balance marginal para un tipo de instrumento.
        """
        if not hasattr(self.api, "marginal_balance_event"):
            self.api.marginal_balance_event = threading.Event()
        
        self.api.marginal_balance_event.clear()
        self.api.get_marginal_balance(instrument_type)
        
        is_ready = self.api.marginal_balance_event.wait(timeout=10.0)
        if is_ready:
            return self.api.marginal_balance.get(instrument_type)
        return None



    def check_cfd_order_capability(self, force=False):
        """
        Probes whether the server accepts place-order-temp messages.
        Returns True if CFD/Forex orders are supported, False otherwise.
        Result is cached after first call.
        """
        if self._cfd_order_capable is not None and not force:
            return self._cfd_order_capable

        get_logger(__name__).info("Probing CFD order capability...")

        # Use well-known OTC pairs from ACTIVES (always open, no need for
        # slow get_all_open_time() call)
        _PROBE_CANDIDATES = [
            ("forex", "EURUSD-OTC"), ("forex", "USDJPY-OTC"),
            ("forex", "GBPUSD-OTC"), ("cfd", "APPLE-OTC"),
            ("crypto", "BTCUSD-OTC"),
        ]
        test_asset = None
        test_type = None
        for cat, name in _PROBE_CANDIDATES:
            if name in OP_code.ACTIVES:
                test_asset = name
                test_type = cat
                break

        if not test_asset:
            # Fallback: use any ACTIVES entry with OTC suffix
            for name in OP_code.ACTIVES:
                if "OTC" in name:
                    test_asset = name
                    test_type = "forex"
                    break

        if not test_asset:
            get_logger(__name__).warning("No OTC assets in ACTIVES to probe CFD capability")
            self._cfd_order_capable = False
            return False

        # Send a minimal order and wait for ANY response (3s timeout)
        self.api.buy_order_id = None
        try:
            self.api.buy_order(
                instrument_type=test_type, instrument_id=test_asset,
                side="buy", amount=1, leverage=1,
                type="market", limit_price=None, stop_price=None,
                stop_lose_value=None, stop_lose_kind=None,
                take_profit_value=None, take_profit_kind=None,
                use_trail_stop=False, auto_margin_call=False,
                use_token_for_commission=False
            )
        except Exception as e:
            get_logger(__name__).warning("CFD probe send failed: %s", e)
            self._cfd_order_capable = False
            return False

        # Fast timeout: 3s instead of 15s
        self.api.order_data_event.clear()
        is_ready = self.api.order_data_event.wait(timeout=3)

        if self.api.buy_order_id is not None:
            get_logger(__name__).info(
                "CFD orders SUPPORTED — probe order_id=%s", self.api.buy_order_id)
            # Close the probe order
            try:
                self.close_position(self.api.buy_order_id)
            except Exception:
                pass
            self._cfd_order_capable = True
        else:
            get_logger(__name__).warning(
                "CFD orders NOT SUPPORTED for this account "
                "(server silently dropped place-order-temp)")
            self._cfd_order_capable = False

        return self._cfd_order_capable

    def buy_order(self, *args, **kwargs):
        try:
            if hasattr(self, "_order_bucket"):
                self._order_bucket.consume()
            return super().buy_order(*args, **kwargs)
        except RateLimitExceededError:
            return False, None

    def change_auto_margin_call(self, ID_Name, ID, auto_margin_call):
        self.api.auto_margin_call_changed_respond_event.clear()
        self.api.change_auto_margin_call(ID_Name, ID, auto_margin_call)
        is_ready = self.api.auto_margin_call_changed_respond_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for auto_margin_call_changed_respond')
            return False, None
        if self.api.auto_margin_call_changed_respond["status"] == 2000:
            return True, self.api.auto_margin_call_changed_respond
        else:
            return False, self.api.auto_margin_call_changed_respond

    def change_order(self, ID_Name, order_id,
                     stop_lose_kind, stop_lose_value,
                     take_profit_kind, take_profit_value,
                     use_trail_stop, auto_margin_call):
        """
        Changes SL/TP of an existing order or position.
        
        Args:
            stop_lose_kind / take_profit_kind accepted values:
              "percent"  -> value is percentage (e.g. 50.0 means 50%)
              "price"    -> value is absolute asset price
              "pnl"      -> value is amount in USD of profit/loss
        
        Example:
            change_order(..., stop_lose_kind="percent", stop_lose_value=50.0,
                              take_profit_kind="percent", take_profit_value=100.0)
        """
        if stop_lose_kind is not None and (stop_lose_value is None or stop_lose_value <= 0):
            return False, "INVALID_PARAMS: stop_lose_value must be > 0 when stop_lose_kind is set"
        if take_profit_kind is not None and (take_profit_value is None or take_profit_value <= 0):
            return False, "INVALID_PARAMS: take_profit_value must be > 0 when take_profit_kind is set"
        if stop_lose_kind is None and take_profit_kind is None:
            get_logger(__name__).warning("change_order called with both SL and TP as None")

        check = True
        if ID_Name == "position_id":
            check, order_data = self.get_order(order_id)
            position_id = order_data["position_id"]
            ID = position_id
        elif ID_Name == "order_id":
            ID = order_id
        else:
            get_logger(__name__).error('change_order input error ID_Name')

        if check:
            self.api.tpsl_changed_respond = None
            self.api.change_order(
                ID_Name=ID_Name, ID=ID,
                stop_lose_kind=stop_lose_kind, stop_lose_value=stop_lose_value,
                take_profit_kind=take_profit_kind, take_profit_value=take_profit_value,
                use_trail_stop=use_trail_stop)
            self.change_auto_margin_call(
                ID_Name=ID_Name, ID=ID, auto_margin_call=auto_margin_call)
            self.api.tpsl_changed_respond_event.clear()
            is_ready = self.api.tpsl_changed_respond_event.wait(timeout=15)
            if not is_ready:
                get_logger(__name__).warning('Timeout (15s) waiting for tpsl_changed_respond')
            if self.api.tpsl_changed_respond["status"] == 2000:
                return True, self.api.tpsl_changed_respond["msg"]
            else:
                return False, self.api.tpsl_changed_respond
        else:
            get_logger(__name__).error('change_order fail to get position_id')
            return False, None

    def get_async_order(self, buy_order_id):
        # S7: Asegurar int-casting para búsqueda en defaultdict/dict
        try:
            buy_order_id = int(buy_order_id)
        except (ValueError, TypeError):
            pass
        # name': 'position-changed', 'microserviceName': "portfolio"/"digital-options"
        return self.api.order_async.get(buy_order_id, {})















    def get_order(self, buy_order_id):
        self.api.order_data_event.clear()
        self.api.get_order(buy_order_id)
        is_ready = self.api.order_data_event.wait(timeout=15)
        if not is_ready or self.api.order_data is None:
            get_logger(__name__).warning('Timeout (15s) waiting for order_data')
            return False, None
        
        if self.api.order_data.get("status") == 2000:
            return True, self.api.order_data.get("msg")
        return True, self.api.order_data

    def get_pending(self, instrument_type):
        self.api.deferred_orders_event.clear()
        self.api.get_pending(instrument_type)
        is_ready = self.api.deferred_orders_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for deferred_orders')
            return False, None
        if self.api.deferred_orders.get("status") == 2000:
            return True, self.api.deferred_orders["msg"]
        else:
            return False, None

    # this function is heavy
    def get_positions(self, *args, **kwargs):
        return super().get_positions(*args, **kwargs)

    def get_position(self, *args, **kwargs):
        return super().get_position(*args, **kwargs)

    def get_digital_position_by_position_id(self, *args, **kwargs):
        return super().get_digital_position_by_position_id(*args, **kwargs)

    def get_digital_position(self, *args, **kwargs):
        return super().get_digital_position(*args, **kwargs)


    def get_position_history_v2(self, *args, **kwargs):
        return super().get_position_history_v2(*args, **kwargs)

    def get_available_leverages(self, *args, **kwargs):
        return super().get_available_leverages(*args, **kwargs)

    def cancel_order(self, *args, **kwargs):
        return super().cancel_order(*args, **kwargs)

    def close_position(self, *args, **kwargs):
        try:
            if hasattr(self, "_order_bucket"):
                self._order_bucket.consume()
            return super().close_position(*args, **kwargs)
        except RateLimitExceededError:
            return False

    def close_position_v2(self, *args, **kwargs):
        return super().close_position_v2(*args, **kwargs)

    def get_overnight_fee(self, *args, **kwargs):
        return super().get_overnight_fee(*args, **kwargs)

    def get_option_open_by_other_pc(self):
        return self.api.socket_option_opened

    def del_option_open_by_other_pc(self, id):
        del self.api.socket_option_opened[id]

    # =================================================================
    # =================== MARGIN TRADING (Modern Protocol) =============
    # =================================================================
    # Uses marginal-{type}.place-market-order (v1.0) — browser-parity
    # Reverse-engineered from Chrome 124 (2026-04-28)
    # =================================================================

    # Mapping from short instrument type to internal prefixes
    _MARGIN_TYPE_MAP = {
        "forex":  "marginal-forex",
        "cfd":    "marginal-cfd",
        "crypto": "marginal-crypto",
        "marginal-forex":  "marginal-forex",
        "marginal-cfd":    "marginal-cfd",
        "marginal-crypto": "marginal-crypto",
    }

    def open_margin_position(
        self,
        instrument_type,      # "forex", "cfd", "crypto"
        active_id,            # Numeric active ID (e.g., 1 for EURUSD)
        direction,            # "buy" or "sell"
        amount,               # Amount in USD (margin)
        leverage,             # Leverage multiplier (e.g., 50, 100, 1000)
        take_profit=None,     # {"type": "pnl"|"price"|"percent", "value": <number>} or None
        stop_loss=None,       # {"type": "pnl"|"price"|"percent", "value": <number>} or None
        timeout=30.0,
    ):
        """
        Opens a margin position using the modern marginal-{type}.place-market-order protocol.

        Args:
            instrument_type: "forex", "cfd", or "crypto"
            active_id: Numeric active ID (e.g., 1 for EURUSD)
            direction: "buy" or "sell"
            amount: Amount in USD (the margin)
            leverage: Leverage multiplier (e.g., 50, 100, 1000)
            take_profit: dict with "type" and "value", or None
                         Example: {"type": "pnl", "value": 5}  -> +$5 profit
                         Example: {"type": "price", "value": 1.17200}
                         Example: {"type": "percent", "value": 50}
            stop_loss: dict with "type" and "value", or None
                       Example: {"type": "pnl", "value": 3}  -> -$3 loss (auto-negated)
                       Example: {"type": "price", "value": 1.16800}
            timeout: Max wait time in seconds

        Returns:
            (True, position_dict) on success
            (False, error_string) on failure
        """
        if amount <= 0:
            return False, "INVALID_PARAMS: amount must be > 0"
        if direction not in ("buy", "sell"):
            return False, f"INVALID_PARAMS: invalid direction '{direction}'"
        if instrument_type.lower() not in self._MARGIN_TYPE_MAP:
            return False, f"INVALID_PARAMS: unknown instrument_type '{instrument_type}'"

        self.api.margin_order_result = None
        self.api.margin_order_event.clear()

        try:
            self.api.place_margin_order(
                instrument_type=instrument_type,
                active_id=active_id,
                side=direction,
                margin=amount,
                leverage=leverage,
                take_profit=take_profit,
                stop_loss=stop_loss,
            )
        except Exception as e:
            get_logger(__name__).error("open_margin_position send failed: %s", e)
            return False, f"SEND_ERROR: {e}"

        # Wait for position confirmation via the 'position' message handler
        is_ready = self.api.margin_order_event.wait(timeout=timeout)

        if is_ready and self.api.margin_order_result is not None:
            order_result = self.api.margin_order_result
            if order_result.get("id") is not None:
                get_logger(__name__).info(
                    "Margin position opened: id=%s type=%s side=%s amount=%s leverage=%s",
                    order_result.get("id"),
                    instrument_type, direction, amount, leverage,
                )
                return True, order_result
            else:
                # Server responded but rejected the order
                return False, f"REJECTED: {order_result.get('error', order_result)}"
        else:
            get_logger(__name__).error(
                "open_margin_position TIMEOUT (%.0fs) for %s %s",
                timeout, instrument_type, direction,
            )
            return False, f"TIMEOUT after {timeout}s"

    def close_margin_position(self, order_id, timeout=15.0):
        """
        Closes a margin position by its order ID.

        """
        # Resolve order_id to position_id and margin type
        position_id, m_type = self._resolve_margin_position_id(order_id)
        
        get_logger(__name__).info("Closing margin position: id=%s (type=%s)", position_id, m_type)

        self.api.close_position_data = None
        self.api.close_position_data_event.clear()
        
        # Modern protocol: marginal-{type}.close-position
        data = {
            "name": f"marginal-{m_type}.close-position",
            "version": "1.0",
            "body": {
                "position_id": int(position_id)
            }
        }
        self.api.send_websocket_request("sendMessage", data)

        start_t = time.time()
        while self.api.close_position_data is None and (time.time() - start_t < timeout):
            self.api.close_position_data_event.wait(timeout=1)
            self.api.close_position_data_event.clear()

        if self.api.close_position_data is not None:
            status = self.api.close_position_data.get("status")
            if status == 2000:
                get_logger(__name__).info("Margin position closed: %s", position_id)
                return True, self.api.close_position_data
            else:
                return False, f"SERVER_ERROR: status={status}"
        return False, f"TIMEOUT after {timeout}s"

    def get_margin_positions(self, instrument_type="forex"):
        """
        Gets all open margin positions for a given instrument type.

        Args:
            instrument_type: "forex", "cfd", or "crypto"

        Returns:
            list of position dicts, or empty list on error
        """
        full_type = self._MARGIN_TYPE_MAP.get(instrument_type.lower(), instrument_type)
        return self.get_open_positions(instrument_type=full_type, timeout=10.0)

    def _resolve_margin_position_id(self, order_id):
        try:
            for m_type in ["marginal-forex", "marginal-cfd", "marginal-crypto"]:
                positions = self.get_open_positions(instrument_type=m_type, timeout=5.0)
                for pos in positions:
                    pos_id = pos.get("id")
                    ext_id = pos.get("external_id")
                    
                    order_ids = []
                    raw_event = pos.get("raw_event", {})
                    for k, v in raw_event.items():
                        if isinstance(v, dict) and "order_ids" in v:
                            order_ids.extend(v["order_ids"])
                    
                    if str(order_id) == str(ext_id) or order_id in order_ids or str(order_id) in [str(o) for o in order_ids]:
                        actual_id = ext_id if ext_id is not None else pos_id
                        m_prefix = m_type.replace("marginal-", "")
                        return actual_id, m_prefix
        except Exception as e:
            get_logger(__name__).warning("Portfolio search failed: %s", e)
        return order_id, "forex" # Default fallback

    def modify_margin_tp_sl(
        self,
        order_id,
        take_profit=None,     # {"type": "pnl", "value": 5} or None
        stop_loss=None,       # {"type": "pnl", "value": 3} or None
    ):
        """
        Modifies TP/SL of an open margin position using the modern protocol.
        """
        position_id, m_type = self._resolve_margin_position_id(order_id)
        
        results = []
        
        # 1. Update Take Profit if provided
        if take_profit is not None:
            get_logger(__name__).info("Updating margin TP: pos=%s, val=%s", position_id, take_profit)
            tp_data = {
                "name": f"marginal-{m_type}.change-position-take-profit-order",
                "version": "1.0",
                "body": {
                    "position_id": int(position_id),
                    "level": {
                        "type": str(take_profit.get("type", "pnl")),
                        "value": float(take_profit.get("value", 0))
                    }
                }
            }
            self.api.result = None
            self.api.result_event.clear()
            self.api.send_websocket_request("sendMessage", tp_data)
            if not self.api.result_event.wait(timeout=10):
                get_logger(__name__).warning("Timeout waiting for TP update result")
                results.append(False)
            else:
                results.append(self.api.result)

        # 2. Update Stop Loss if provided
        if stop_loss is not None:
            get_logger(__name__).info("Updating margin SL: pos=%s, val=%s", position_id, stop_loss)
            sl_value = float(stop_loss.get("value", 0))
            # Ensure negative for pnl type if positive value provided
            if str(stop_loss.get("type", "pnl")) == "pnl" and sl_value > 0:
                sl_value = -abs(sl_value)
                
            sl_data = {
                "name": f"marginal-{m_type}.change-position-stop-loss-order",
                "version": "2.0",
                "body": {
                    "position_id": int(position_id),
                    "level": {
                        "type": str(stop_loss.get("type", "pnl")),
                        "value": sl_value
                    },
                    "trailing_stop": bool(stop_loss.get("trailing_stop", False))
                }
            }
            self.api.result = None
            self.api.result_event.clear()
            self.api.send_websocket_request("sendMessage", sl_data)
            if not self.api.result_event.wait(timeout=10):
                get_logger(__name__).warning("Timeout waiting for SL update result")
                results.append(False)
            else:
                results.append(self.api.result)

        if not results:
            return True, "NO_CHANGES"
            
        final_success = all(results)
        return final_success, {"results": results}

    def get_available_leverages(self, *args, **kwargs):
        return super().get_available_leverages(*args, **kwargs)

    def get_min_leverage(self, instrument_type, active_id):
        """
        Retrieves the minimum required leverage for a specific asset.
        """
        full_type = self._MARGIN_TYPE_MAP.get(instrument_type.lower(), instrument_type)
        if not full_type.startswith("marginal-"):
            full_type = f"marginal-{full_type}"

        # 1. Get the instrument metadata
        self.get_open_positions(instrument_type=full_type, timeout=5.0) # Ensure sync
        
        instrument_data = self._get_instrument_data(full_type, active_id)
        if not instrument_data:
            return 1 # Fallback

        leverage_profile_id = instrument_data.get("leverage_profile_id")
        if leverage_profile_id is None:
            return 1

        # 2. Lookup in dynamic leverage profiles
        profile = getattr(self.api, "dynamic_leverage_profiles", {}).get(leverage_profile_id)
        if profile:
            return profile.get("min_leverage", 1)
            
        return 1

    def _get_instrument_data(self, instrument_type, active_id):
        """
        Helper to find instrument details in the stored metadata.
        """
        if not hasattr(self.api, "instruments") or not self.api.instruments:
            return None
            
        items = self.api.instruments.get("instruments", [])
        for item in items:
            if item.get("active_id") == active_id:
                return item
        return None

    # =================================================================

    def opcode_to_name(self, opcode):
        return list(OP_code.ACTIVES.keys())[list(OP_code.ACTIVES.values()).index(opcode)]

    # name:
    # "live-deal-binary-option-placed"
    # "live-deal-digital-option"
    def subscribe_live_deal(self, *args, **kwargs):
        return super().subscribe_live_deal(*args, **kwargs)

    def unsubscribe_live_deal(self, *args, **kwargs):
        return super().unsubscribe_live_deal(*args, **kwargs)

    def unscribe_live_deal(self, name, active, _type):
        get_logger(__name__).warning(
            "unscribe_live_deal() is deprecated, use unsubscribe_live_deal()")
        return self.unsubscribe_live_deal(name, active, _type)

    def set_digital_live_deal_cb(self, cb):
        self.api.digital_live_deal_cb = cb

    def set_binary_live_deal_cb(self, cb):
        self.api.binary_live_deal_cb = cb

    def get_live_deal(self, name, active, _type):
        return self.api.live_deal_data[name][active][_type]

    def pop_live_deal(self, name, active, _type):
        return self.api.live_deal_data[name][active][_type].pop()

    def clear_live_deal(self, name, active, _type, buffersize):
        self.api.live_deal_data[name][active][_type] = deque(
            list(), buffersize)

    def get_user_profile_client(self, user_id):
        self.api.user_profile_client_event.clear()
        self.api.Get_User_Profile_Client(user_id)
        is_ready = self.api.user_profile_client_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for user_profile_client')
        return self.api.user_profile_client

    def request_leaderboard_userinfo_deals_client(self, user_id, country_id):
        self.api.leaderboard_userinfo_deals_client_event.clear()
        self.api.Request_Leaderboard_Userinfo_Deals_Client(user_id, country_id)
        is_ready = self.api.leaderboard_userinfo_deals_client_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for leaderboard_userinfo')
        return self.api.leaderboard_userinfo_deals_client

    def get_users_availability(self, user_id):
        self.api.users_availability_event.clear()
        self.api.Get_Users_Availability(user_id)
        is_ready = self.api.users_availability_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for users_availability')
        return self.api.users_availability

    def get_digital_payout(self, active, seconds=0):
        asset_id = OP_code.ACTIVES[active]
        
        # SPRINT 6: Check trading_params_data first (cached payout)
        if hasattr(self.api, "trading_params_data") and asset_id in self.api.trading_params_data:
            data = self.api.trading_params_data[asset_id]
            if time.time() - data.get("updated_at", 0) < 60:
                payout = data.get("payout")
                if payout:
                    return int(payout)

        self.api.digital_payout = None

        self.api.subscribe_digital_price_splitter(asset_id)

        is_ready = self.api.digital_payout_event.wait(timeout=seconds or config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for digital_payout")

        try:
            self.api.unsubscribe_digital_price_splitter(asset_id)
        except Exception:
            pass

        return self.api.digital_payout if self.api.digital_payout else 0

    def get_payout(self, active):
        """
        SPRINT 6: Retorna payout de un activo (int).
        Intenta usar trading-params cache, fallback a digital.
        """
        active_id = None
        if active in OP_code.ACTIVES:
            active_id = OP_code.ACTIVES[active]
        
        if active_id and hasattr(self.api, "trading_params_data") and active_id in self.api.trading_params_data:
            data = self.api.trading_params_data[active_id]
            if time.time() - data.get("updated_at", 0) < 60:
                payout = data.get("payout")
                if payout:
                    return int(payout)
        
        return self.get_digital_payout(active)

    def logout(self):
        self.api.logout()

    @rate_limited("_order_bucket")
    # ══════════════════════════════════════════════════════════════════
    #  SPRINT 1 — Portfolio Control
    # ══════════════════════════════════════════════════════════════════

    def get_all_open_positions(self, *args, **kwargs):
        return super().get_all_open_positions(*args, **kwargs)

    # ── S1-T2: Reconciler ──────────────────────────────────────────

    def reconcile_missed_results(self, since_ts: float) -> dict:
        """
        Recupera resultados de trades que expiraron durante una desconexión.
        Llamar SIEMPRE al reconectar si había trades abiertos.

        Args:
            since_ts: Unix timestamp de inicio del período a reconciliar
        Returns:
            {order_id: "win" | "loose" | "equal" | "unknown"}
        Note:
            "loose" is the IQ Option server typo — NOT a bug.
        """
        return self._reconciler.reconcile(since_ts)

    # ── S1-T3: Generic Order Status ───────────────────────────────

    def get_order_status(
        self,
        order_id: int,
        instrument_type: str
    ):
        """
        Consulta el estado de una orden por ID sin importar su tipo.
        instrument_type: "binary" | "turbo" | "digital" | "blitz" | "cfd" | "forex" | "crypto"

        Retorna dict con al menos: {id, status, result, invest, close_profit}
        Retorna None si no se puede obtener el estado.
        """
        _binary_types = {"binary", "turbo", "blitz"}
        _digital_types = {"digital"}
        _cfd_types = {"cfd", "forex", "crypto"}

        itype = instrument_type.lower().replace("-option", "").replace("-", "")

        if itype in _binary_types:
            success, data = self.get_betinfo(order_id)
            if success and data:
                return {
                    "id": order_id,
                    "type": instrument_type,
                    "status": "closed" if data.get("result") else "open",
                    "result": data.get("result"),
                    "invest": data.get("amount"),
                    "close_profit": data.get("win_amount"),
                    "raw": data
                }

        elif itype in _digital_types or itype in _cfd_types:
            # Para digitales y CFD usar get_async_order
            order_data = self.get_async_order(order_id)
            if order_data and order_data.get("position-changed"):
                msg = order_data["position-changed"].get("msg", {})
                return {
                    "id": order_id,
                    "type": instrument_type,
                    "status": msg.get("status", "unknown"),
                    "result": msg.get("close_reason"),
                    "invest": msg.get("invest"),
                    "close_profit": msg.get("close_profit") or msg.get("pnl_realized"),
                    "raw": msg
                }

        get_logger(__name__).warning(
            "get_order_status: no data found for order_id=%s type=%s",
            order_id, instrument_type
        )
        return None

    # ── S2-T1: Blitz Trading ──────────────────────────────────────

    @rate_limited("_order_bucket")

    # ── S3: Memory & Stream Stabilization ─────────────────────────

    def _start_maintenance_thread(self):
        def _run():
            while not self._stop_event.is_set():
                # Esperar 1 hora entre limpiezas
                if self._stop_event.wait(timeout=3600):
                    break
                if hasattr(self, 'candle_cache'):
                    n = self.candle_cache.evict_expired()
                    if n > 0:
                        get_logger(__name__).info("candle_cache: evicted %d expired candles", n)
        
        t = threading.Thread(target=_run, name="candle-maintenance", daemon=True)
        t.start()

    def subscribe_candle_v2(self, *args, **kwargs):
        return super().subscribe_candle_v2(*args, **kwargs)

    def unsubscribe_candle_v2(self, *args, **kwargs):
        return super().unsubscribe_candle_v2(*args, **kwargs)
