# python
from iqoptionapi.api import IQOptionAPI
import iqoptionapi.constants as OP_code
import iqoptionapi.country_id as Country
import threading
import time
import json
from iqoptionapi.logger import get_logger
from iqoptionapi.reconnect import ReconnectManager, MaxReconnectAttemptsError
from iqoptionapi.idempotency import IdempotencyRegistry
from iqoptionapi.security import CredentialStore, generate_user_agent
from iqoptionapi.ratelimit import TokenBucket, RateLimitExceededError, rate_limited
from iqoptionapi.config import (
    TIMEOUT_WS_DATA, TIMEOUT_CANDLE_STREAM, TIMEOUT_SSID_AUTH,
    TIMEOUT_BALANCE_RESET, TIMEOUT_ALL_INIT
)
from iqoptionapi.http.session import close_shared_session
import iqoptionapi
import logging
import operator
from collections import deque
from iqoptionapi.utils import nested_dict
from iqoptionapi.expiration import get_expiration_time, get_remaning_time
from datetime import datetime, timedelta
from random import randint




class IQ_Option:
    __version__ = iqoptionapi.__version__

    def __init__(self, email, password, active_account_type="PRACTICE"):
        self.size = [1, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800,
                     3600, 7200, 14400, 28800, 43200, 86400, 604800, 2592000]
        self.email = email
        self._credential_store = CredentialStore(email, password)
        self._reconnect_manager = ReconnectManager()
        self._idempotency = IdempotencyRegistry()
        self._order_bucket = TokenBucket(block=True)
        # BUG-DIGITAL-01: Initialize missing event stores on api instance
        # These are used by the new non-blocking _wait_result helper
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
        self.SESSION_HEADER = {
            "User-Agent": generate_user_agent()}
        self.SESSION_COOKIE = {}
        #


    # --------------------------------------------------------------------------

    def get_server_timestamp(self):
        return self.api.timesync.server_timestamp

    def re_subscribe_stream(self):
        for ac in self.subscribe_candle:
                    sp = ac.split(",")
                    self.start_candles_one_stream(sp[0], sp[1])
        # -----------------
        for ac in self.subscribe_candle_all_size:
                    self.start_candles_all_size_stream(ac)
        # -------------reconnect subscribe_mood
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

    def connect(self, sms_code=None):
        if hasattr(self, 'api') and hasattr(self.api, 'websocket_client'):
            try:
                self.api.close()
            except Exception:
                pass

        self.api = IQOptionAPI(
            "ws.iqoption.com", self.email)
        
        # Initialize event stores required for non-blocking result waits
        from collections import defaultdict
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

        check, reason = self.api.connect(self._credential_store.consume())
        if check:
            # Register callbacks for resilience (S1-03)
            self.api._reconnect_callback = self._auto_reconnect
            self.api._heartbeat_callback = lambda: setattr(self, '_last_heartbeat', __import__('time').time())
            
            self._reconnect_manager.reset()
            self._idempotency.purge_expired()

        if check == True:
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


            self._start_heartbeat_watchdog()
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

    def _auto_reconnect(self) -> None:
        """
        Auto-reconexión con backoff exponencial.
        Llamado por WebsocketClient.on_close() en thread daemon.
        Usa self._reconnect_manager para controlar intentos y delays.
        """
        from iqoptionapi.reconnect import MaxReconnectAttemptsError
        logger = get_logger(__name__)
        logger.info("Auto-reconnect started.")

        while True:
            try:
                self._reconnect_manager.wait()   # backoff + jitter
            except MaxReconnectAttemptsError:
                logger.critical(
                    "Auto-reconnect: max attempts exhausted. "
                    "Bot requires manual intervention."
                )
                return

            logger.info(
                "Auto-reconnect: attempt %d/%d (waiting finished)",
                self._reconnect_manager.attempts,
                self._reconnect_manager._max
            )

            try:
                logger.info("Auto-reconnect: calling self.connect()...")
                status, reason = self.connect()
                if status:
                    logger.info("Auto-reconnect: SUCCESS.")
                    self._reconnect_manager.reset()
                    return
                else:
                    logger.warning("Auto-reconnect: connect() failed: %s", reason)
            except Exception as e:
                logger.error("Auto-reconnect: exception during connect(): %s", e)

    def _start_heartbeat_watchdog(self) -> None:
        """
        Inicia un thread daemon que monitorea el heartbeat del servidor.
        Si no llega un heartbeat en HEARTBEAT_TIMEOUT_SECS segundos,
        fuerza reconexión llamando a _auto_reconnect().
        """
        import threading, time
        from iqoptionapi.config import HEARTBEAT_TIMEOUT_SECS, HEARTBEAT_CHECK_INTERVAL

        self._last_heartbeat = time.time()
        self._watchdog_stop = threading.Event()

        def watchdog_loop():
            while not self._watchdog_stop.is_set():
                time.sleep(HEARTBEAT_CHECK_INTERVAL)
                elapsed = time.time() - self._last_heartbeat
                if elapsed > HEARTBEAT_TIMEOUT_SECS:
                    get_logger(__name__).warning(
                        "Heartbeat watchdog: %.0fs sin heartbeat — forzando reconexión",
                        elapsed
                    )
                    self._last_heartbeat = time.time()  # reset para evitar bucle
                    t = threading.Thread(
                        target=self._auto_reconnect, daemon=True,
                        name="WatchdogReconnect"
                    )
                    t.start()

        self._watchdog_thread = threading.Thread(
            target=watchdog_loop, daemon=True, name="HeartbeatWatchdog"
        )
        self._watchdog_thread.start()
        get_logger(__name__).info("Heartbeat watchdog started.")

    def _stop_heartbeat_watchdog(self) -> None:
        """Detiene el watchdog. Llamar en IQ_Option.close()."""
        if hasattr(self, '_watchdog_stop'):
            self._watchdog_stop.set()
        if hasattr(self, '_watchdog_thread'):
            self._watchdog_thread.join(timeout=2.0)

    def check_connect(self):
        # True/False
        # if not connected, sometimes it's None, sometimes its '0', so
        # both will fall on this first case
        if not self.api.check_websocket_if_connect:
            return False
        else:
            return True
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
        for ins in instruments["instruments"]:
            OP_code.ACTIVES[ins["id"]] = ins["active_id"]

    def instruments_input_all_in_ACTIVES(self):
        self.instruments_input_to_ACTIVES("crypto")
        self.instruments_input_to_ACTIVES("forex")
        self.instruments_input_to_ACTIVES("cfd")

    def get_ALL_Binary_ACTIVES_OPCODE(self):
        init_info = self.get_all_init()
        for dirr in (["binary", "turbo"]):
            for i in init_info["result"][dirr]["actives"]:
                OP_code.ACTIVES[(init_info["result"][dirr]
                                 ["actives"][i]["name"]).split(".")[1]] = int(i)

    # _________________________self.api.get_api_option_init_all() wss______________
    def get_all_init(self):
        if hasattr(self.api, 'api_option_init_all_result_event'):
            self.api.api_option_init_all_result = None
            self.api.api_option_init_all_result_event.clear()
            self.api.get_api_option_init_all()
            is_ready = self.api.api_option_init_all_result_event.wait(timeout=TIMEOUT_ALL_INIT)
            if not is_ready or self.api.api_option_init_all_result is None:
                get_logger(__name__).warning("Timeout or disconnect: api_option_init_all_result unavailable")
        self.api.api_option_init_all_result_event.clear()
        self.api.get_api_option_init_all()
        is_ready = self.api.api_option_init_all_result_event.wait(timeout=10)
        return self.api.api_option_init_all_result if is_ready else None

    def get_all_init_v2(self):
        self.api.api_option_init_all_result_v2_event.clear()
        if self.check_connect() == False:
            self.connect()
        self.api.get_api_option_init_all_v2()
        is_ready = self.api.api_option_init_all_result_v2_event.wait(timeout=TIMEOUT_ALL_INIT)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for api_option_init_all_result_v2")
        return self.api.api_option_init_all_result_v2

    # ------- chek if binary/digit/cfd/stock... if open or not

    def __get_binary_open(self):
        # for turbo and binary pairs
        binary_data = self.get_all_init_v2()
        binary_list = ["binary", "turbo"]
        if binary_data:
            for option in binary_list:
                if option in binary_data:
                    for actives_id in binary_data[option]["actives"]:
                        active = binary_data[option]["actives"][actives_id]
                        name = str(active["name"]).split(".")[1]
                        if active["enabled"] == True:
                            if active["is_suspended"] == True:
                                self.OPEN_TIME[option][name]["open"] = False
                            else:
                                self.OPEN_TIME[option][name]["open"] = True
                        else:
                            self.OPEN_TIME[option][name]["open"] = active["enabled"]    

    def __get_digital_open(self):
        # for digital options
        digital_data = []
        for _ in range(3):
            data = self.get_digital_underlying_list_data()
            if isinstance(data, dict) and "underlying" in data:
                digital_data = data.get("underlying", [])
            elif isinstance(data, list):
                digital_data = data
            
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

    def __get_other_open(self):
        # Crypto and etc pairs
        instrument_list = ["cfd", "forex", "crypto"]
        for instruments_type in instrument_list:
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
        self.api.profile_msg_event.clear()
        self.api.getprofile()
        is_ready = self.api.profile_msg_event.wait(timeout=TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for profile")
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
        return self.api.balances_raw

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

    def reset_practice_balance(self):
        self.api.training_balance_reset_request_event.clear()
        self.api.reset_training_balance()
        is_ready = self.api.training_balance_reset_request_event.wait(timeout=TIMEOUT_BALANCE_RESET)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for training_balance_reset_request")
        return self.api.training_balance_reset_request

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

    def change_balance(self, Balance_MODE):
        def set_id(b_id):
            if hasattr(self.api, 'balance_id') and self.api.balance_id != None:
                self.position_change_all(
                    "unsubscribeMessage", self.api.balance_id)

            self.api.balance_id = b_id

            self.position_change_all("subscribeMessage", b_id)

        real_id = None
        practice_id = None
        tournament_id = None

        for balance in self.get_profile_ansyc()["balances"]:
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

    # ________________________________________________________________________
    # _______________________        CANDLE      _____________________________
    # ________________________self.api.getcandles() wss________________________

    def get_candles(self, ACTIVES, interval, count, endtime):
        if ACTIVES not in OP_code.ACTIVES:
            get_logger(__name__).error("Asset %s not found in ACTIVES", ACTIVES)
            return None

        self.api.candles_event.clear()
        try:
            self.api.getcandles(OP_code.ACTIVES[ACTIVES], interval, count, endtime)
        except Exception as e:
            get_logger(__name__).error("get_candles request error: %s", e)
            return None

        is_ready = self.api.candles_event.wait(timeout=TIMEOUT_WS_DATA)
        if not is_ready or self.api.candles.candles_data is None:
            get_logger(__name__).warning("Timeout or disconnect: candles data unavailable")
            return None
        return self.api.candles.candles_data

    #######################################################
    # ______________________________________________________
    # _____________________REAL TIME CANDLE_________________
    # ______________________________________________________
    #######################################################

    def start_candles_stream(self, ACTIVE, size, maxdict):

        if size == "all":
            for s in self.size:
                self.full_realtime_get_candle(ACTIVE, s, maxdict)
                self.api.real_time_candles_maxdict_table[ACTIVE][s] = maxdict
            self.start_candles_all_size_stream(ACTIVE)
        elif size in self.size:
            self.api.real_time_candles_maxdict_table[ACTIVE][size] = maxdict
            self.full_realtime_get_candle(ACTIVE, size, maxdict)
            self.start_candles_one_stream(ACTIVE, size)

        else:
            get_logger(__name__).error(
                '**error** start_candles_stream please input right size')

    def stop_candles_stream(self, ACTIVE, size):
        if size == "all":
            self.stop_candles_all_size_stream(ACTIVE)
        elif size in self.size:
            self.stop_candles_one_stream(ACTIVE, size)
        else:
            get_logger(__name__).error(
                '**error** start_candles_stream please input right size')

    def get_realtime_candles(self, ACTIVE, size):
        if size == "all":
            try:
                return self.api.real_time_candles[ACTIVE]
            except Exception as e:
                get_logger(__name__).error(
                    '**error** get_realtime_candles() size="all" can not get candle')
                return False
        elif size in self.size:
            try:
                return self.api.real_time_candles[ACTIVE][size]
            except Exception as e:
                get_logger(__name__).error(
                    '**error** get_realtime_candles() size=' + str(size) + ' can not get candle')
                return False
        else:
            get_logger(__name__).error(
                '**error** get_realtime_candles() please input right "size"')

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
    def start_candles_one_stream(self, ACTIVE, size):
        if not (ACTIVE in self.api.real_time_candles and size in self.api.real_time_candles[ACTIVE]):
            self.api.subscribe(OP_code.ACTIVES[ACTIVE], size)
            
        # BUG-SPINLOOP-02: Migrado a Event+timeout
        start_t = time.time()
        while not self.api.candle_generated_check.get(str(ACTIVE), {}).get(int(size)) and (time.time() - start_t < 20.0):
            self.api.candles_event.wait(timeout=1.0)
            self.api.candles_event.clear()
            
        return self.api.candle_generated_check.get(str(ACTIVE), {}).get(int(size)) == True

    def stop_candles_one_stream(self, ACTIVE, size):
        if ((ACTIVE + "," + str(size)) in self.subscribe_candle) == True:
            self.subscribe_candle.remove(ACTIVE + "," + str(size))
        
        # BUG-SPINLOOP-02: Migrado a Event+timeout
        self.api.candle_generated_check[str(ACTIVE)][int(size)] = {}
        self.api.unsubscribe(OP_code.ACTIVES[ACTIVE], size)
        
        start_t = time.time()
        while self.api.candle_generated_check.get(str(ACTIVE), {}).get(int(size)) != {} and (time.time() - start_t < 20.0):
            time.sleep(0.1)
        return True

    # ------------------------Subscribe ALL SIZE-----------------------

    def start_candles_all_size_stream(self, ACTIVE):
        self.api.candle_generated_all_size_check[str(ACTIVE)] = {}
        if (str(ACTIVE) in self.subscribe_candle_all_size) == False:
            self.subscribe_candle_all_size.append(str(ACTIVE))
        
        # BUG-SPINLOOP-03: Migrado a Event+timeout
        self.api.subscribe_all_size(OP_code.ACTIVES[ACTIVE])
        start_t = time.time()
        while not self.api.candle_generated_all_size_check.get(str(ACTIVE)) and (time.time() - start_t < 20.0):
            self.api.candles_event.wait(timeout=1.0)
            self.api.candles_event.clear()
            
        return self.api.candle_generated_all_size_check.get(str(ACTIVE)) == True

    def stop_candles_all_size_stream(self, ACTIVE):
        if (str(ACTIVE) in self.subscribe_candle_all_size) == True:
            self.subscribe_candle_all_size.remove(str(ACTIVE))
        
        # BUG-SPINLOOP-03: Refactorizado para evitar while True
        self.api.candle_generated_all_size_check[str(ACTIVE)] = {}
        self.api.unsubscribe_all_size(OP_code.ACTIVES[ACTIVE])
        
        start_t = time.time()
        while self.api.candle_generated_all_size_check.get(str(ACTIVE)) != {} and (time.time() - start_t < 10.0):
            time.sleep(0.1)
        return True

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

    def start_mood_stream(self, ACTIVES, instrument="turbo-option"):
        self.api.subscribe_Traders_mood(ACTIVES, instrument)
        
        # BUG-SPINLOOP-06: Migrar a Event+timeout
        start_t = time.time()
        while not self.api.traders_mood and (time.time() - start_t < 20.0):
            self.api.result_event.wait(timeout=1.0)
            self.api.result_event.clear()
        
        return True

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
        is_ready = self.api.technical_indicators_event.wait(timeout=TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for technical_indicators: %s", ACTIVES)
        return self.api.technical_indicators.get(str(ACTIVES))

##############################################################################################

    # ── Non-blocking Result Helper ────────────────────────────
    def _wait_result(
        self,
        order_id: int,
        result_store,
        event_store: dict,
        timeout: float = 120.0,
    ) -> dict | None:
        """Espera el resultado de un trade sin bloquear el thread forever.
        
        Retorna el dict del resultado, o None si vence el timeout.
        """
        event: threading.Event = event_store.get(order_id, threading.Event())
        fired = event.wait(timeout=timeout)
        if not fired:
            return None
        
        # Si el result_store tiene un método get_id_data (como listinfodata)
        if hasattr(result_store, "get_id_data"):
            return result_store.get_id_data(order_id)
        return result_store.get(order_id)

##############################################################################################

    def check_binary_order(self, order_id, timeout=30.0):
        # BUG-SPINLOOP-01: Migrado a Event+timeout
        start_t = time.time()
        while order_id not in self.api.order_binary and (time.time() - start_t < timeout):
            self.api.option_closed_event.wait(timeout=1.0)
            self.api.option_closed_event.clear()
        return self.api.order_binary.pop(order_id, None)

    def check_win(self, id_number, timeout=120.0):
        # BUG-SPINLOOP-01: Refactorizado a _wait_result para evitar while True
        result = self._wait_result(
            order_id=id_number,
            result_store=self.api.listinfodata,
            event_store=self.api.result_event_store,
            timeout=timeout
        )
        if result:
            self.api.listinfodata.delete(id_number)
            return result.get("win", None)
        return None

    def check_win_v2(self, id_number, timeout=120.0):
        # BUG-SPINLOOP-01: Refactorizado
        result = self._wait_result(
            order_id=id_number,
            result_store=self.api.game_betinfo,
            event_store=self.api.game_betinfo_event,
            timeout=timeout
        )
        if result:
            return result.get("game_state")
        return None

    def check_win_v4(self, id_number, timeout=120.0):
        # BUG-SPINLOOP-01: Refactorizado a _wait_result
        return self._wait_result(
            order_id=id_number,
            result_store=self.api.socket_option_closed,
            event_store=self.api.socket_option_closed_event,
            timeout=timeout
        )

    def check_win_v3(self, id_number, timeout=120.0):
        # BUG-SPINLOOP-01: Refactorizado a _wait_result
        result = self._wait_result(
            order_id=id_number,
            result_store=self.api.socket_option_closed,
            event_store=self.api.socket_option_closed_event,
            timeout=timeout
        )
        if result:
            return result.get("msg", {}).get("win")
        return None

    # -------------------get infomation only for binary option------------------------

    def get_betinfo(self, id_number):
        # INPUT:int
        if not hasattr(self.api, "game_betinfo_event"):
            self.api.game_betinfo_event = threading.Event()
            
        self.api.game_betinfo.isSuccessful = None
        self.api.game_betinfo_event.clear()
        
        try:
            self.api.get_betinfo(id_number)
        except Exception as e:
            get_logger(__name__).error('**error** def get_betinfo  self.api.get_betinfo reconnect')
            return False, None
            
        is_ready = self.api.game_betinfo_event.wait(timeout=10)
        
        if not is_ready:
            get_logger(__name__).warning('**error** get_betinfo time out')
            return False, None
            
        return self.api.game_betinfo.isSuccessful, self.api.game_betinfo.dict

    def get_optioninfo(self, limit):
        self.api.api_game_getoptions_result_event.clear()
        self.api.get_options(limit)
        is_ready = self.api.api_game_getoptions_result_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for api_game_getoptions_result')
        return self.api.api_game_getoptions_result

    def get_optioninfo_v2(self, limit):
        self.api.get_options_v2_data_event.clear()
        self.api.get_options_v2(limit, "binary,turbo")
        is_ready = self.api.get_options_v2_data_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for get_options_v2_data')
        return self.api.get_options_v2_data

    # __________________________BUY__________________________

    # __________________FOR OPTION____________________________

    @rate_limited("_order_bucket")
    def buy_multi(self, price, ACTIVES, ACTION, expirations):
        self.api.buy_multi_option = {}
        if len(price) == len(ACTIVES) == len(ACTION) == len(expirations):
            buy_len = len(price)
            for idx in range(buy_len):
                self.api.buyv3(
                    price[idx], OP_code.ACTIVES[ACTIVES[idx]], ACTION[idx], expirations[idx], idx)
            while len(self.api.buy_multi_option) < buy_len:
                self.api.result_event.wait(timeout=1)
                self.api.result_event.clear()
            buy_id = []
            for key in sorted(self.api.buy_multi_option.keys()):
                try:
                    value = self.api.buy_multi_option[str(key)]
                    buy_id.append(value["id"])
                except Exception:
                    buy_id.append(None)

            return buy_id
        else:
            get_logger(__name__).error('buy_multi error please input all same len')

    def get_remaning(self, duration):
        for remaning in get_remaning_time(self.api.timesync.server_timestamp):
            if remaning[0] == duration:
                return remaning[1]
        get_logger(__name__).error('get_remaning(self,duration) ERROR duration')
        return "ERROR duration"

    def buy_by_raw_expirations(self, price, active, direction, option, expired):
        self.api.buy_multi_option = {}
        self.api.result_event.clear()
        req_id = str(randint(0, 10000))
        self.api.buy_multi_option[req_id] = {"id": None}
        self.api.buyv3_by_raw_expirations(
            float(price), OP_code.ACTIVES[active], str(direction), str(option), int(expired), req_id)
        
        is_ready = self.api.result_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for buy_by_raw_expirations result")
        
        id = self.api.buy_multi_option.get(req_id, {}).get("id")
        return self.api.result, id

    @rate_limited("_order_bucket")
    def buy(self, price, ACTIVES, ACTION, expirations):
        request_id = self._idempotency.register()
        get_logger(__name__).info(
            "buy(): request_id=%s | asset=%s | action=%s | amount=%s",
            request_id, ACTIVES, ACTION, price
        )
        self.api.buy_multi_option = {}
        self.api.result_event.clear()
        req_id = str(randint(0, 10000))
        self.api.buy_multi_option[req_id] = {"id": None}
        self.api.buyv3(
            float(price), OP_code.ACTIVES[ACTIVES], str(ACTION), int(expirations), req_id)
        
        is_ready = self.api.result_event.wait(timeout=15)
        
        id = self.api.buy_multi_option.get(req_id, {}).get("id")
        if id is None:
            if self.api.buy_multi_option.get(req_id, {}).get("message"):
                self._idempotency.fail(request_id)
                return False, self.api.buy_multi_option[req_id]["message"]
            if not is_ready:
                self._idempotency.fail(request_id)
                get_logger(__name__).critical("buy() TIMEOUT: request_id=%s", request_id)
                return False, None
        
        self._idempotency.confirm(request_id, id)
        return self.api.result, id

    @rate_limited("_order_bucket")
    def sell_option(self, options_ids):
        self.api.sold_options_respond_event.clear()
        self.api.sell_option(options_ids)
        is_ready = self.api.sold_options_respond_event.wait(timeout=30)
        if not is_ready:
            get_logger(__name__).error("Timeout waiting for sell_option response.")
            return None
        return self.api.sold_options_respond

    @rate_limited("_order_bucket")
    def sell_digital_option(self, options_ids):
        # BUG-DIGITAL-01: Migrado de _rate_limiter a _order_bucket via decorador
        self.api.result_event.clear()
        self.api.sell_digital_option(options_ids)
        is_ready = self.api.result_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for sell_digital_option_respond')
        return self.api.sold_digital_options_respond
# __________________for Digital___________________

    def get_digital_underlying_list_data(self):
        self.api.underlying_list_data_event.clear()
        self.api.get_digital_underlying()
        is_ready = self.api.underlying_list_data_event.wait(timeout=TIMEOUT_WS_DATA)
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

    def subscribe_strike_list(self, ACTIVE, expiration_period):
        self.api.subscribe_instrument_quites_generated(
            ACTIVE, expiration_period)

    def unsubscribe_strike_list(self, ACTIVE, expiration_period):
        del self.api.instrument_quites_generated_data[ACTIVE]
        self.api.unsubscribe_instrument_quites_generated(
            ACTIVE, expiration_period)

    def get_instrument_quites_generated_data(self, ACTIVE, duration):
        start_t = time.time()
        while self.api.instrument_quotes_generated_raw_data[ACTIVE][duration * 60] == {} and (time.time() - start_t < 15.0):
            self.api.instrument_quotes_generated_event.wait(timeout=1)
            self.api.instrument_quotes_generated_event.clear()
        return self.api.instrument_quotes_generated_raw_data[ACTIVE][duration * 60]

    def get_realtime_strike_list(self, ACTIVE, duration):
        start_t = time.time()
        while not self.api.instrument_quites_generated_data[ACTIVE][duration * 60] and (time.time() - start_t < 15.0):
            self.api.instrument_quotes_generated_event.wait(timeout=1)
            self.api.instrument_quotes_generated_event.clear()

        ans = {}
        now_timestamp = self.api.instrument_quites_generated_timestamp[ACTIVE][duration * 60]

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

            profit = self.api.instrument_quites_generated_data[ACTIVE][duration * 60]
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
        profit = self.api.instrument_quites_generated_data[ACTIVE][duration * 60]
        for key in profit:
            if key.find("SPT") != -1:
                return profit[key]
        return False

    
    @rate_limited("_order_bucket")
    def buy_digital_spot(self, active, amount, action, duration):
        # BUG-DIGITAL-02: Migrado de _rate_limiter a _order_bucket
        """
        DEPRECATED: Use buy_digital_spot_v2() instead. This method uses
        the legacy instrument_id format which may be rejected by the server.
        """
        # Expiration time need to be formatted like this: YYYYMMDDHHII
        # And need to be on GMT time

        # Type - P or C
        action = action.lower()
        if action == 'put':
            action = 'P'
        elif action == 'call':
            action = 'C'
        else:
            get_logger(__name__).error('buy_digital_spot active error')
            return -1, None
        
        exp, _ = get_expiration_time(int(self.api.timesync.server_timestamp), duration)
        dateFormated = str(datetime.utcfromtimestamp(exp).strftime("%Y%m%d%H%M"))
        instrument_id = "do" + active + dateFormated + "PT" + str(duration) + "M" + action + "SPT"

        self.api.digital_option_placed_id_event.clear()
        request_id = self.api.place_digital_option(instrument_id, amount)

        is_ready = self.api.digital_option_placed_id_event.wait(timeout=15)
        digital_order_id = self.api.digital_option_placed_id.get(request_id)
        
        if not is_ready or digital_order_id is None:
            get_logger(__name__).warning('Timeout (15s) waiting for digital_option_placed_id')
            return False, digital_order_id
            
        return True, digital_order_id

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
        instrument_quites_generated_data = self.get_instrument_quites_generated_data(
            ACTIVES, duration)


        f_tmp = get_instrument_id_to_bid(
            instrument_quites_generated_data, aVar)
        # f is bidprice of lower_instrument_id ,f2 is bidprice of upper_instrument_id
        if f_tmp != None:
            self.get_digital_spot_profit_after_sale_data[position_id]["f"] = f_tmp
            f = f_tmp
        else:
            f = self.get_digital_spot_profit_after_sale_data[position_id]["f"]

        f2_tmp = get_instrument_id_to_bid(
            instrument_quites_generated_data, aVar2)
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

    def buy_digital(self, amount, instrument_id):
        self.api.digital_option_placed_id_event.clear()
        request_id = self.api.place_digital_option(instrument_id, amount)
        is_ready = self.api.digital_option_placed_id_event.wait(timeout=30)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for buy_digital")
        return self.api.digital_option_placed_id.get(request_id)

    @rate_limited("_order_bucket")
    def close_digital_option(self, position_id):
        # Wait for position info
        while self.get_async_order(position_id).get("position-changed") == {}:
            is_ready = self.api.position_changed_event.wait(timeout=TIMEOUT_WS_DATA)
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

    def check_win_digital(self, buy_order_id, timeout=120.0):
        # BUG-SPINLOOP-01: Refactorizado para usar _wait_result con timeout
        # Nota: digital usa position_changed_event para notificar cierres
        result = self._wait_result(
            order_id=buy_order_id,
            result_store=self.api.digital_option_placed_id, # Almacén de resultados digital
            event_store=self.api.position_changed_event_store,
            timeout=timeout
        )
        if result and result.get("msg") and result["msg"].get("position", {}).get("status") == "closed":
            pos = result["msg"]["position"]
            if pos["close_reason"] == "default":
                return pos["pnl_realized"]
            elif pos["close_reason"] == "expired":
                return pos["pnl_realized"] - pos["buy_amount"]
        return None

    def check_win_digital_v2(self, buy_order_id, timeout=120.0):
        # BUG-SPINLOOP-01: Refactorizado
        result = self._wait_result(
            order_id=buy_order_id,
            result_store=None, # Usamos get_async_order que ya consulta el store correcto
            event_store=self.api.position_changed_event_store,
            timeout=timeout
        )
        
        order_data = self.get_async_order(buy_order_id).get("position-changed", {}).get("msg")
        if order_data:
            if order_data["status"] == "closed":
                if order_data["close_reason"] == "expired":
                    return True, order_data["close_profit"] - order_data["invest"]
                elif order_data["close_reason"] == "default":
                    return True, order_data["pnl_realized"]
            return False, None
        return False, None

    # ----------------------------------------------------------
    # -----------------BUY_for__Forex__&&__stock(cfd)__&&__ctrpto

    # ── CFD/Forex/Crypto order capability detection ──
    # Some user groups (e.g. user_group_id:191) have place-order-temp
    # silently disabled server-side. This flag caches the probe result.
    _cfd_order_capable = None  # None=untested, True/False=tested

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

    @rate_limited("_order_bucket")
    def buy_order(self,
                  instrument_type,
                  instrument_id,
                  side,
                  amount,
                  leverage,
                  type,
                  limit_price=None,
                  stop_price=None,
                  take_profit_kind=None,
                  take_profit_value=None,
                  stop_lose_kind=None,
                  stop_lose_value=None,
                  use_trail_stop=False,
                  auto_margin_call=False,
                  use_token_for_commission=False):
        # BUG-STABILITY: Migrado de _rate_limiter manual a decorador
        if amount <= 0:
            return False, "INVALID_PARAMS: amount must be > 0"
        if side not in ("buy", "sell"):
            return False, f"INVALID_PARAMS: invalid side '{side}'"
        if type not in ("market", "limit", "stop"):
            return False, f"INVALID_PARAMS: invalid type '{type}'"
        if stop_lose_kind is not None and (stop_lose_value is None or stop_lose_value <= 0):
            return False, "INVALID_PARAMS: stop_lose_value must be > 0 when stop_lose_kind is set"
        if take_profit_kind is not None and (take_profit_value is None or take_profit_value <= 0):
            return False, "INVALID_PARAMS: take_profit_value must be > 0 when take_profit_kind is set"
        if type == "limit" and limit_price is None:
            return False, "INVALID_PARAMS: limit_price cannot be None for limit orders"
        if type == "stop" and stop_price is None:
            return False, "INVALID_PARAMS: stop_price cannot be None for stop orders"

        if self._cfd_order_capable is False:
            return False, "CFD_NOT_SUPPORTED: place-order-temp disabled for this account"

        request_id = self._idempotency.register()
        self.api.buy_order_id = None
        self.api.order_data_event.clear()
        
        self.api.buy_order(
            instrument_type=instrument_type, instrument_id=instrument_id,
            side=side, amount=amount, leverage=leverage,
            type=type, limit_price=limit_price, stop_price=stop_price,
            stop_lose_value=stop_lose_value, stop_lose_kind=stop_lose_kind,
            take_profit_value=take_profit_value, take_profit_kind=take_profit_kind,
            use_trail_stop=use_trail_stop, auto_margin_call=auto_margin_call,
            use_token_for_commission=use_token_for_commission
        )

        is_ready = self.api.order_data_event.wait(timeout=15)
        if not is_ready or self.api.buy_order_id is None:
            self._idempotency.fail(request_id)
            if self._cfd_order_capable is None:
                self._cfd_order_capable = False
            get_logger(__name__).critical("buy_order() TIMEOUT: request_id=%s", request_id)
            return False, "TIMEOUT"

        self._idempotency.confirm(request_id, self.api.buy_order_id)
        if self._cfd_order_capable is None:
            self._cfd_order_capable = True
        return True, self.api.buy_order_id

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
        # name': 'position-changed', 'microserviceName': "portfolio"/"digital-options"
        return self.api.order_async[buy_order_id]

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
    def get_positions(self, instrument_type):
        self.api.positions_event.clear()
        self.api.get_positions(instrument_type)
        is_ready = self.api.positions_event.wait(timeout=TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for positions")
            return False, None
        
        if self.api.positions.get("status") == 2000:
            return True, self.api.positions["msg"]
        else:
            return False, None

    def get_position(self, buy_order_id):
        check, order_data = self.get_order(buy_order_id)
        if not check: return False, None
        position_id = order_data["position_id"]
        self.api.position_event.clear()
        self.api.get_position(position_id)
        is_ready = self.api.position_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for position')
            return False, None
        if self.api.position.get("status") == 2000:
            return True, self.api.position["msg"]
        else:
            return False, None

    def get_digital_position_by_position_id(self, position_id):
        self.api.position_event.clear()
        self.api.get_digital_position(position_id)
        is_ready = self.api.position_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for digital position')
        return self.api.position

    def get_digital_position(self, order_id):
        # Note: digital-position often requires waiting for position-changed or similar
        # For simplicity, we keep the sync part but use events for the final fetch
        start_t = time.time()
        while self.get_async_order(order_id).get("position-changed") == {} and (time.time() - start_t < 15.0):
            time.sleep(0.05)
            pass
        position_id = self.get_async_order(order_id)["position-changed"]["msg"]["external_id"]
        return self.get_digital_position_by_position_id(position_id)

    def get_position_history(self, instrument_type):
        self.api.position_history_event.clear()
        self.api.get_position_history(instrument_type)
        is_ready = self.api.position_history_event.wait(timeout=TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for position_history")
            return False, None

        if self.api.position_history.get("status") == 2000:
            return True, self.api.position_history["msg"]
        else:
            return False, None

    def get_position_history_v2(self, instrument_type, limit, offset, start, end):
        self.api.position_history_v2_event.clear()
        self.api.get_position_history_v2(instrument_type, limit, offset, start, end)
        is_ready = self.api.position_history_v2_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for position_history_v2')
            return False, None
        if self.api.position_history_v2.get("status") == 2000:
            return True, self.api.position_history_v2["msg"]
        else:
            return False, None

    def get_available_leverages(self, instrument_type, actives=""):
        self.api.available_leverages_event.clear()
        if actives == "":
            self.api.get_available_leverages(instrument_type, "")
        else:
            self.api.get_available_leverages(instrument_type, OP_code.ACTIVES[actives])
        is_ready = self.api.available_leverages_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for available_leverages')
            return False, None
        if self.api.available_leverages.get("status") == 2000:
            return True, self.api.available_leverages["msg"]
        else:
            return False, None

    def cancel_order(self, buy_order_id):
        self.api.order_canceled_event.clear()
        self.api.cancel_order(buy_order_id)
        is_ready = self.api.order_canceled_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for order_canceled')
            return False
        return self.api.order_canceled.get("status") == 2000

    @rate_limited("_order_bucket")
    def close_position(self, position_id):
        # BUG-STABILITY: Migrado a decorador
        check, data = self.get_order(position_id)
        if check and data.get("position_id") != None:
            self.api.close_position_data_event.clear()
            self.api.close_position(data["position_id"])
            start_t = time.time()
            while self.api.close_position_data == None and (time.time() - start_t < 15.0):
                self.api.close_position_data_event.wait(timeout=1)
                self.api.close_position_data_event.clear()
            return self.api.close_position_data is not None and self.api.close_position_data.get("status") == 2000
        return False

    def close_position_v2(self, position_id):
        _ts = time.time()
        while self.get_async_order(position_id) == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for get_async_order(position_id)')
                break
            pass
        position_changed = self.get_async_order(position_id)
        self.api.close_position(position_changed["id"])
        _ts = time.time()
        while self.api.close_position_data == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for close_position_data')
                break
            pass
        if self.api.close_position_data["status"] == 2000:
            return True
        else:
            return False

    def get_overnight_fee(self, instrument_type, active):
        self.api.overnight_fee_event.clear()
        self.api.get_overnight_fee(instrument_type, OP_code.ACTIVES[active])
        is_ready = self.api.overnight_fee_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for overnight_fee')
            return False, None
        if self.api.overnight_fee.get("status") == 2000:
            return True, self.api.overnight_fee["msg"]
        else:
            return False, None

    def get_option_open_by_other_pc(self):
        return self.api.socket_option_opened

    def del_option_open_by_other_pc(self, id):
        del self.api.socket_option_opened[id]

    # -----------------------------------------------------------------

    def opcode_to_name(self, opcode):
        return list(OP_code.ACTIVES.keys())[list(OP_code.ACTIVES.values()).index(opcode)]

    # name:
    # "live-deal-binary-option-placed"
    # "live-deal-digital-option"
    def subscribe_live_deal(self, name, active, _type, buffersize):
        active_id = OP_code.ACTIVES[active]
        self.api.Subscribe_Live_Deal(name, active_id, _type)

    def unsubscribe_live_deal(self, name, active, _type):
        active_id = OP_code.ACTIVES[active]
        self.api.Unscribe_Live_Deal(name, active_id, _type)

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
        self.api.digital_payout = None
        asset_id = OP_code.ACTIVES[active]

        self.api.subscribe_digital_price_splitter(asset_id)

        is_ready = self.api.digital_payout_event.wait(timeout=seconds or TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for digital_payout")

        self.api.unsubscribe_digital_price_splitter(asset_id)

        return self.api.digital_payout if self.api.digital_payout else 0

    def logout(self):
        self.api.logout()

    @rate_limited("_order_bucket")
    def buy_digital_spot_v2(self, active, amount, action, duration):
        action = action.lower()

        if action == 'put':
            action = 'P'
        elif action == 'call':
            action = 'C'
        else:
            get_logger(__name__).error('buy_digital_spot_v2 active error')
            return -1, None

        timestamp = int(self.api.timesync.server_timestamp)

        if duration == 1:
            exp, _ = get_expiration_time(timestamp, duration)
        else:
            now_date = datetime.fromtimestamp(
                timestamp) + timedelta(minutes=1, seconds=30)

            while True:
                time.sleep(0.05)
                if now_date.minute % duration == 0 and time.mktime(now_date.timetuple()) - timestamp > 30:
                    break
                now_date = now_date + timedelta(minutes=1)

            exp = time.mktime(now_date.timetuple())

        date_formated = str(datetime.utcfromtimestamp(exp).strftime("%Y%m%d%H%M"))
        active_id = str(OP_code.ACTIVES[active])
        instrument_id = "do" + active_id + "A" + \
            date_formated[:8] + "D" + date_formated[8:] + \
            "00T" + str(duration) + "M" + action + "SPT"
        logger = get_logger(__name__)
        logger.info(instrument_id)
        request_id = self.api.place_digital_option_v2(instrument_id, active_id, amount)

        is_ready = self.api.digital_option_placed_id_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).error('Timeout (15s) waiting for digital_option_placed_id')
            return False, None
        digital_order_id = self.api.digital_option_placed_id.get(request_id)
        if isinstance(digital_order_id, int):
            return True, digital_order_id
        else:
            return False, digital_order_id
