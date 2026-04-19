# python
from iqoptionapi.api import IQOptionAPI
import iqoptionapi.constants as OP_code
import iqoptionapi.country_id as Country
import threading
import time
import json
from iqoptionapi.logger import get_logger
from iqoptionapi.security import CredentialStore, generate_user_agent
import logging
import operator
from collections import defaultdict
from collections import deque
from iqoptionapi.expiration import get_expiration_time, get_remaning_time
from iqoptionapi.version_control import api_version
from datetime import datetime, timedelta
from random import randint


def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n - 1, type))


class IQ_Option:
    __version__ = api_version

    def __init__(self, email, password, active_account_type="PRACTICE"):
        self.size = [1, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800,
                     3600, 7200, 14400, 28800, 43200, 86400, 604800, 2592000]
        self.email = email
        self._credential_store = CredentialStore(email, password)
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
        # --start
        # self.connect()
        # this auto function delay too long

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

    def connect(self, sms_code=None):
        if hasattr(self, 'api') and hasattr(self.api, 'websocket_client'):
            try:
                self.api.close()
            except Exception:
                pass

        self.api = IQOptionAPI(
            "iqoption.com", self.email)
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

            """
            self.api.subscribe_position_changed(
                "position-changed", "multi-option", 2)

            self.api.subscribe_position_changed(
                "trading-fx-option.position-changed", "fx-option", 3)

            self.api.subscribe_position_changed(
                "position-changed", "crypto", 4)

            self.api.subscribe_position_changed(
                "position-changed", "forex", 5)

            self.api.subscribe_position_changed(
                "digital-options.position-changed", "digital-option", 6)

            self.api.subscribe_position_changed(
                "position-changed", "cfd", 7)
            """

            # Auto-update asset catalogs on successful connection
            try:
                self.update_ACTIVES_OPCODE()
                get_logger(__name__).info("Live Asset Catalogs (Binary, Crypto, Forex, CFD) successfully synchronized.")
            except Exception as e:
                get_logger(__name__).warning("Failed to auto-update asset catalogs: %s", e)

            # self.get_balance_id()
            return True, None
        else:
            if json.loads(reason)['code'] == 'verify':
                response = self.api.send_sms_code(json.loads(reason)['token'])

                if response.json()['code'] != 'success':
                    return False, response.json()['message']

                # token_sms
                self.resp_sms = response
                return False, "2FA"
            return False, reason

    # self.update_ACTIVES_OPCODE()

    def connect_2fa(self, sms_code):
        return self.connect(sms_code=sms_code)

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
        self.api.Get_Leader_Board(country_id, user_country_id, from_position, to_position,
                                  near_traders_country_count, near_traders_count, top_country_count, top_count, top_type)

        _ts = time.time()
        while self.api.leaderboard_deals_client == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for leaderboard_deals_client')
                break
            pass
        return self.api.leaderboard_deals_client

    def get_instruments(self, type):
        # type="crypto"/"forex"/"cfd"
        time.sleep(self.suspend)
        self.api.instruments = None
        self.api.instruments_event.clear()
        
        try:
            if hasattr(self.api, 'instruments_event'):
                self.api.instruments_event.clear()
            
            self.api.get_instruments(type)
            
            if hasattr(self.api, 'instruments_event'):
                is_ready = self.api.instruments_event.wait(timeout=10)
                if not is_ready:
                    get_logger(__name__).warning("Timeout waiting for instruments of type: %s", type)
                    return {"instruments": []} # Return empty list gracefully instead of None
        except Exception as e:
                get_logger(__name__).error('**error** api.get_instruments need reconnect: %s', e)
                # self.connect() # Removed aggressive recursive connect
        return getattr(self.api, 'instruments', {"instruments": []})

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

    # _________________________self.api.get_api_option_init_all() wss______________________
    def get_all_init(self):

        while True:
            time.sleep(0.05)
            self.api.api_option_init_all_result = None
            while True:
                time.sleep(0.05)
                try:
                    self.api.get_api_option_init_all()
                    break
                except Exception as e:
                    get_logger(__name__).error('**error** get_all_init need reconnect')
                    self.connect()
                    time.sleep(5)
            start = time.time()
            while True:
                time.sleep(0.05)
                if time.time() - start > 30:
                    get_logger(__name__).error('**warning** get_all_init late 30 sec')
                    break
                try:
                    if self.api.api_option_init_all_result != None:
                        break
                except (KeyError, TypeError) as e:
                    get_logger(__name__).error("Data extraction error: %s", e)
            if getattr(self.api, "api_option_init_all_result", {}).get("isSuccessful") == True:
                    return self.api.api_option_init_all_result

    def get_all_init_v2(self):
        self.api.api_option_init_all_result_v2 = None

        if self.check_connect() == False:
            self.connect()

        self.api.get_api_option_init_all_v2()
        start_t = time.time()
        while self.api.api_option_init_all_result_v2 == None:
            time.sleep(0.05)
            if time.time() - start_t >= 30:
                get_logger(__name__).error('**warning** get_all_init_v2 late 30 sec')
                return None
        return self.api.api_option_init_all_result_v2

        # return OP_code.ACTIVES

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
        data = self.get_digital_underlying_list_data()
        digital_data = data.get("underlying", []) if data else []
        for digital in digital_data:
            name = digital["underlying"]
            schedule = digital["schedule"]
            self.OPEN_TIME["digital"][name]["open"] = False
            for schedule_time in schedule:
                start = schedule_time["open"]
                end = schedule_time["close"]
                if start < time.time() < end:
                    self.OPEN_TIME["digital"][name]["open"] = True

    def __get_other_open(self):
        # Crypto and etc pairs
        instrument_list = ["cfd", "forex", "crypto"]
        for instruments_type in instrument_list:
            ins_data = self.get_instruments(instruments_type)["instruments"]
            for detail in ins_data:
                name = detail["name"]
                schedule = detail["schedule"]
                self.OPEN_TIME[instruments_type][name]["open"] = False
                for schedule_time in schedule:
                    start = schedule_time["open"]
                    end = schedule_time["close"]
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
        if self.api.profile.msg is not None:
            return self.api.profile.msg
            
        if hasattr(self.api, 'profile_msg_event'):
            self.api.profile_msg_event.clear()
            is_ready = self.api.profile_msg_event.wait(timeout=30)
            if not is_ready:
                get_logger(__name__).error("Timeout waiting for profile ansyc.")
                return None
        return self.api.profile.msg

    """def get_profile(self):
        while True:
            time.sleep(0.05)
            try:

                respon = self.api.getprofile().json()
                time.sleep(self.suspend)

                if respon["isSuccessful"] == True:
                    return respon
            except Exception as e:
                get_logger(__name__).error('**error** get_profile try reconnect')
                self.connect()"""

    def get_currency(self):
        balances_raw = self.get_balances()
        for balance in balances_raw["msg"]:
            if balance["id"] == self.api.balance_id:
                return balance["currency"]

    def get_balance_id(self):
        return self.api.balance_id

    """ def get_balance(self):
        self.api.profile.balance = None
        while True:
            time.sleep(0.05)
            try:
                respon = self.get_profile()
                self.api.profile.balance = respon["result"]["balance"]
                break
            except Exception as e:
                get_logger(__name__).error('**error** get_balance()')

            time.sleep(self.suspend)
        return self.api.profile.balance"""

    def get_balance(self):

        balances_raw = self.get_balances()
        for balance in balances_raw["msg"]:
            if balance["id"] == self.api.balance_id:
                return balance["amount"]

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
        self.api.training_balance_reset_request = None
        self.api.reset_training_balance()
        _ts = time.time()
        while self.api.training_balance_reset_request == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for training_balance_reset_request')
                break
            pass
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
        self.api.candles.candles_data = None
        while True:
            time.sleep(0.05)
            try:
                if ACTIVES not in OP_code.ACTIVES:
                    get_logger(__name__).info('Asset {} not found on consts'.format(ACTIVES))
                    break
                self.api.getcandles(
                    OP_code.ACTIVES[ACTIVES], interval, count, endtime)
                
                if hasattr(self.api, 'candles_event'):
                    self.api.candles_event.wait(timeout=20)
                
                if self.api.candles.candles_data != None:
                    break
            except Exception as e:
                get_logger(__name__).error('**error** get_candles need reconnect: %s', e)
                self.connect()

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
        if (str(ACTIVE + "," + str(size)) in self.subscribe_candle) == False:
            self.subscribe_candle.append((ACTIVE + "," + str(size)))
        start = time.time()
        self.api.candle_generated_check[str(ACTIVE)][int(size)] = {}
        while True:
            time.sleep(0.05)
            if time.time() - start > 20:
                get_logger(__name__).error(
                    '**error** start_candles_one_stream late for 20 sec')
                return False
            if self.api.candle_generated_check.get(str(ACTIVE), {}).get(int(size)) == True:
                    return True
            try:

                self.api.subscribe(OP_code.ACTIVES[ACTIVE], size)
            except Exception as e:
                get_logger(__name__).error('**error** start_candles_stream reconnect')
                self.connect()
            time.sleep(1)

    def stop_candles_one_stream(self, ACTIVE, size):
        if ((ACTIVE + "," + str(size)) in self.subscribe_candle) == True:
            self.subscribe_candle.remove(ACTIVE + "," + str(size))
        while True:
            time.sleep(0.05)
            if self.api.candle_generated_check.get(str(ACTIVE), {}).get(int(size)) == {}:
                    return True
            self.api.candle_generated_check[str(ACTIVE)][int(size)] = {}
            self.api.unsubscribe(OP_code.ACTIVES[ACTIVE], size)
            time.sleep(self.suspend * 10)

    # ------------------------Subscribe ALL SIZE-----------------------

    def start_candles_all_size_stream(self, ACTIVE):
        self.api.candle_generated_all_size_check[str(ACTIVE)] = {}
        if (str(ACTIVE) in self.subscribe_candle_all_size) == False:
            self.subscribe_candle_all_size.append(str(ACTIVE))
        start = time.time()
        while True:
            time.sleep(0.05)
            if time.time() - start > 20:
                get_logger(__name__).error('**error** fail ' + ACTIVE +
                              ' start_candles_all_size_stream late for 10 sec')
                return False
            if self.api.candle_generated_all_size_check.get(str(ACTIVE)) == True:
                    return True
            try:
                self.api.subscribe_all_size(OP_code.ACTIVES[ACTIVE])
            except Exception as e:
                get_logger(__name__).error(
                    '**error** start_candles_all_size_stream reconnect')
                self.connect()
            time.sleep(1)

    def stop_candles_all_size_stream(self, ACTIVE):
        if (str(ACTIVE) in self.subscribe_candle_all_size) == True:
            self.subscribe_candle_all_size.remove(str(ACTIVE))
        while True:
            time.sleep(0.05)
            if self.api.candle_generated_all_size_check.get(str(ACTIVE)) == {}:
                    break
            self.api.candle_generated_all_size_check[str(ACTIVE)] = {}
            self.api.unsubscribe_all_size(OP_code.ACTIVES[ACTIVE])
            time.sleep(self.suspend * 10)

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
        if ACTIVES in self.subscribe_mood == False:
            self.subscribe_mood.append(ACTIVES)

        while True:
            time.sleep(0.05)
            self.api.subscribe_Traders_mood(
                OP_code.ACTIVES[ACTIVES], instrument)
            try:
                self.api.traders_mood[OP_code.ACTIVES[ACTIVES]]
                break
            except Exception as e:
                time.sleep(5)

    def stop_mood_stream(self, ACTIVES, instrument="turbo-option"):
        if ACTIVES in self.subscribe_mood == True:
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
        request_id = self.api.get_Technical_indicators(
            OP_code.ACTIVES[ACTIVES])
        _ts = time.time()
        while self.api.technical_indicators.get(request_id) == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for technical_indicators')
                break
            pass
        return self.api.technical_indicators[request_id]

##############################################################################################


##############################################################################################

    def check_binary_order(self, order_id):
        _ts = time.time()
        # Binary options can have expirations up to 1-2 hours or more for end-of-day.
        # We wait up to 120 minutes max, or until the option closes.
        while order_id not in self.api.order_binary:
            time.sleep(0.05)
            if time.time() - _ts >= 7200:
                get_logger(__name__).warning('Timeout (120 min) waiting for order_id to close in binary options')
                return None
        your_order = self.api.order_binary.pop(order_id, None)
        return your_order

    def check_win(self, id_number):
        # 'win':win money 'equal':no win no loose   'loose':loose money
        listinfodata_dict = None
        _ts = time.time()
        while True:
            time.sleep(0.05)
            if time.time() - _ts >= 7200:
                get_logger(__name__).warning('Timeout (120 min) waiting for check_win')
                break
            try:
                listinfodata_dict = self.api.listinfodata.get(id_number)
                if listinfodata_dict["game_state"] == 1:
                    break
            except Exception:
                pass
        self.api.listinfodata.delete(id_number)
        if listinfodata_dict is not None:
            return listinfodata_dict.get("win", None)
        return None

    def check_win_v2(self, id_number, polling_time):
        _ts = time.time()
        while True:
            time.sleep(0.05)
            if time.time() - _ts >= 7200:
                get_logger(__name__).warning('Timeout (120 min) waiting for check_win_v2')
                return None
            check, data = self.get_betinfo(id_number)
            if check and data and "result" in data and "data" in data["result"]:
                win = data["result"]["data"][str(id_number)].get("win", "")
                if win != "":
                    try:
                        return data["result"]["data"][str(id_number)]["profit"] - data["result"]["data"][str(id_number)]["deposit"]
                    except (KeyError, TypeError) as e:
                        get_logger(__name__).error("Data extraction error: %s", e)
            time.sleep(polling_time)

        
    def check_win_v4(self, id_number):
        _ts = time.time()
        while True:
            time.sleep(0.05)
            if time.time() - _ts >= 7200:
                get_logger(__name__).warning('Timeout (120 min) waiting for check_win_v4')
                return None, None
            if self.api.socket_option_closed.get(id_number) != None:
                    break
        x = self.api.socket_option_closed[id_number]
        return x['msg']['win'], (0 if x['msg']['win'] == 'equal' else float(x['msg']['sum']) * -1 if x['msg']['win'] == 'loose' else float(x['msg']['win_amount']) - float(x['msg']['sum']))

    def check_win_v3(self, id_number):
        _ts = time.time()
        while True:
            time.sleep(0.05)
            if time.time() - _ts >= 7200:
                get_logger(__name__).warning('Timeout (120 min) waiting for check_win_v3')
                return None, None
            result = self.get_optioninfo_v2(10)
            if result and result.get('msg') and result['msg'].get('closed_options'):
                try:
                    if result['msg']['closed_options'][0]['id'][0] == id_number and result['msg']['closed_options'][0]['id'][0] != None:
                        return result['msg']['closed_options'][0]['win'], (result['msg']['closed_options'][0]['win_amount'] - result['msg']['closed_options'][0]['amount'] if result['msg']['closed_options'][0]['win'] != 'equal' else 0)
                except Exception:
                    pass
            time.sleep(1)

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
        self.api.api_game_getoptions_result = None
        self.api.get_options(limit)
        _ts = time.time()
        while self.api.api_game_getoptions_result == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for api_game_getoptions_result')
                break
            pass

        return self.api.api_game_getoptions_result

    def get_optioninfo_v2(self, limit):
        self.api.get_options_v2_data = None
        self.api.get_options_v2(limit, "binary,turbo")
        _ts = time.time()
        while self.api.get_options_v2_data == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for get_options_v2_data')
                break
            pass

        return self.api.get_options_v2_data

    # __________________________BUY__________________________

    # __________________FOR OPTION____________________________

    def buy_multi(self, price, ACTIVES, ACTION, expirations):
        self.api.buy_multi_option = {}
        if len(price) == len(ACTIVES) == len(ACTION) == len(expirations):
            buy_len = len(price)
            for idx in range(buy_len):
                self.api.buyv3(
                    price[idx], OP_code.ACTIVES[ACTIVES[idx]], ACTION[idx], expirations[idx], idx)
            while len(self.api.buy_multi_option) < buy_len:
                time.sleep(0.05)
                pass
            buy_id = []
            for key in sorted(self.api.buy_multi_option.keys()):
                try:
                    value = self.api.buy_multi_option[str(key)]
                    buy_id.append(value["id"])
                except Exception as e:
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
        self.api.buy_successful = None
        req_id = "buyraw"
        self.api.buy_multi_option[req_id] = {"id": None}
        self.api.buyv3_by_raw_expired(
            price, OP_code.ACTIVES[active], direction, option, expired, request_id=req_id)
        start_t = time.time()
        id = None
        self.api.result = None
        _ts = time.time()
        while self.api.result == None or id == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for result')
                break
            try:
                if "message" in self.api.buy_multi_option[req_id].keys():
                    get_logger(__name__).error(
                        '**warning** buy' + str(self.api.buy_multi_option[req_id]["message"]))
                    return False, self.api.buy_multi_option[req_id]["message"]
            except Exception:
                pass
            id = self.api.buy_multi_option.get(req_id, {}).get("id")
            if time.time() - start_t >= 5:
                get_logger(__name__).error('**warning** buy late 5 sec')
                return False, None

        return self.api.result, self.api.buy_multi_option[req_id]["id"]

    def buy(self, price, ACTIVES, ACTION, expirations):
        self.api.buy_multi_option = {}
        self.api.buy_successful = None
        # req_id = "buy"
        req_id = str(randint(0, 10000))
        self.api.buy_multi_option[req_id] = {"id": None}
        self.api.buyv3(
            float(price), OP_code.ACTIVES[ACTIVES], str(ACTION), int(expirations), req_id)
        start_t = time.time()
        id = None
        self.api.result = None
        while self.api.result == None or id == None:
            time.sleep(0.05)
            if self.api.buy_multi_option.get(req_id, {}).get("message"):
                    return False, self.api.buy_multi_option[req_id]["message"]
            id = self.api.buy_multi_option.get(req_id, {}).get("id")
            if time.time() - start_t >= 5:
                get_logger(__name__).error('**warning** buy late 5 sec')
                return False, None

        return self.api.result, self.api.buy_multi_option[req_id]["id"]

    def sell_option(self, options_ids):
        self.api.sold_options_respond = None
        if hasattr(self.api, 'sold_options_respond_event'):
            self.api.sold_options_respond_event.clear()
            
        self.api.sell_option(options_ids)
        
        if hasattr(self.api, 'sold_options_respond_event'):
            is_ready = self.api.sold_options_respond_event.wait(timeout=30)
            if not is_ready:
                get_logger(__name__).error("Timeout waiting for sell_option response.")
                return None
                
        return self.api.sold_options_respond

    def sell_digital_option(self, options_ids):
        self.api.sell_digital_option(options_ids)
        self.api.sold_digital_options_respond = None
        _ts = time.time()
        while self.api.sold_digital_options_respond == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for sold_digital_options_respond')
                break
            pass
        return self.api.sold_digital_options_respond
# __________________for Digital___________________

    def get_digital_underlying_list_data(self):
        self.api.underlying_list_data = None
        self.api.get_digital_underlying()
        start_t = time.time()
        while self.api.underlying_list_data == None:
            time.sleep(0.05)
            if time.time() - start_t >= 30:
                get_logger(__name__).error(
                    '**warning** get_digital_underlying_list_data late 30 sec')
                return None

        return self.api.underlying_list_data

    def get_strike_list(self, ACTIVES, duration):
        self.api.strike_list = None
        self.api.get_strike_list(ACTIVES, duration)
        ans = {}
        _ts = time.time()
        while self.api.strike_list == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for strike_list')
                break
            pass
        try:
            for data in self.api.strike_list["msg"]["strike"]:
                temp = {}
                temp["call"] = data["call"]["id"]
                temp["put"] = data["put"]["id"]
                ans[("%.6f" % (float(data["value"]) * 10e-7))] = temp
        except (KeyError, TypeError) as e:
            get_logger(__name__).error('**error** get_strike_list read problem: %s', e)
            return getattr(self.api, 'strike_list', None), None
        return self.api.strike_list, ans

    def subscribe_strike_list(self, ACTIVE, expiration_period):
        self.api.subscribe_instrument_quites_generated(
            ACTIVE, expiration_period)

    def unsubscribe_strike_list(self, ACTIVE, expiration_period):
        del self.api.instrument_quites_generated_data[ACTIVE]
        self.api.unsubscribe_instrument_quites_generated(
            ACTIVE, expiration_period)

    def get_instrument_quites_generated_data(self, ACTIVE, duration):
        while self.api.instrument_quotes_generated_raw_data[ACTIVE][duration * 60] == {}:
            time.sleep(0.05)
            pass
        return self.api.instrument_quotes_generated_raw_data[ACTIVE][duration * 60]

    def get_realtime_strike_list(self, ACTIVE, duration):
        while True:
            time.sleep(0.05)
            if not self.api.instrument_quites_generated_data[ACTIVE][duration * 60]:
                pass
            else:
                break
        """
        strike_list dict: price:{call:id,put:id}
        """
        ans = {}
        now_timestamp = self.api.instrument_quites_generated_timestamp[ACTIVE][duration * 60]

        while ans == {}:
            time.sleep(0.05)
            if self.get_realtime_strike_list_temp_data == {} or now_timestamp != self.get_realtime_strike_list_temp_expiration:
                raw_data, strike_list = self.get_strike_list(ACTIVE, duration)
                self.get_realtime_strike_list_temp_expiration = raw_data["msg"]["expiration"]
                self.get_realtime_strike_list_temp_data = strike_list
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

        return ans

    def get_digital_current_profit(self, ACTIVE, duration):
        profit = self.api.instrument_quites_generated_data[ACTIVE][duration * 60]
        for key in profit:
            if key.find("SPT") != -1:
                return profit[key]
        return False

    
    def buy_digital_spot(self, active, amount, action, duration):
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
        # doEURUSD201907191250PT5MPSPT
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

        dateFormated = str(datetime.utcfromtimestamp(
            exp).strftime("%Y%m%d%H%M"))
        instrument_id = "do" + active + dateFormated + \
                        "PT" + str(duration) + "M" + action + "SPT"
        # self.api.digital_option_placed_id = None

        request_id = self.api.place_digital_option(instrument_id, amount)

        _ts = time.time()
        while self.api.digital_option_placed_id.get(request_id) == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for digital_option_placed_id')
                break
            pass
        digital_order_id = self.api.digital_option_placed_id.get(request_id)
        if isinstance(digital_order_id, int):
            return True, digital_order_id
        else:
            return False, digital_order_id

        # while self.api.digital_option_placed_id == None:
        #     pass
        # if isinstance(self.api.digital_option_placed_id, int):
        #     return True, self.api.digital_option_placed_id
        # else:
        #     return False, self.api.digital_option_placed_id

    def get_digital_spot_profit_after_sale(self, position_id):
        def get_instrument_id_to_bid(data, instrument_id):
            for row in data["msg"]["quotes"]:
                if row["symbols"][0] == instrument_id:
                    return row["price"]["bid"]
            return None

        while self.get_async_order(position_id)["position-changed"] == {}:
            time.sleep(0.05)
            pass
        # ___________________/*position*/_________________
        position = self.get_async_order(position_id)["position-changed"]["msg"]
        # doEURUSD201911040628PT1MPSPT
        # z mean check if call or not
        if position["instrument_id"].find("MPSPT"):
            z = False
        elif position["instrument_id"].find("MCSPT"):
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
        self.api.digital_option_placed_id = None
        self.api.place_digital_option(instrument_id, amount)
        start_t = time.time()
        while self.api.digital_option_placed_id == None:
            time.sleep(0.05)
            if time.time() - start_t > 30:
                get_logger(__name__).error('buy_digital loss digital_option_placed_id')
                return False, None
        return True, self.api.digital_option_placed_id

    def close_digital_option(self, position_id):
        self.api.result = None
        while self.get_async_order(position_id)["position-changed"] == {}:
            time.sleep(0.05)
            pass
        position_changed = self.get_async_order(
            position_id)["position-changed"]["msg"]
        self.api.close_digital_option(position_changed["external_id"])
        _ts = time.time()
        while self.api.result == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for result')
                break
            pass
        return self.api.result

    def check_win_digital(self, buy_order_id, polling_time):
        while True:
            time.sleep(0.05)
            time.sleep(polling_time)
            data = self.get_digital_position(buy_order_id)

            if data["msg"]["position"]["status"] == "closed":
                if data["msg"]["position"]["close_reason"] == "default":
                    return data["msg"]["position"]["pnl_realized"]
                elif data["msg"]["position"]["close_reason"] == "expired":
                    return data["msg"]["position"]["pnl_realized"] - data["msg"]["position"]["buy_amount"]

    def check_win_digital_v2(self, buy_order_id):

        while self.get_async_order(buy_order_id)["position-changed"] == {}:
            time.sleep(0.05)
            pass
        order_data = self.get_async_order(
            buy_order_id)["position-changed"]["msg"]
        if order_data != None:
            if order_data["status"] == "closed":
                if order_data["close_reason"] == "expired":
                    return True, order_data["close_profit"] - order_data["invest"]
                elif order_data["close_reason"] == "default":
                    return True, order_data["pnl_realized"]
            else:
                return False, None
        else:
            return False, None

    # ----------------------------------------------------------
    # -----------------BUY_for__Forex__&&__stock(cfd)__&&__ctrpto

    def buy_order(self,
                  instrument_type, instrument_id,
                  side, amount, leverage,
                  type, limit_price=None, stop_price=None,

                  stop_lose_kind=None, stop_lose_value=None,
                  take_profit_kind=None, take_profit_value=None,

                  use_trail_stop=False, auto_margin_call=False,
                  use_token_for_commission=False):
        self.api.buy_order_id = None
        self.api.buy_order(
            instrument_type=instrument_type, instrument_id=instrument_id,
            side=side, amount=amount, leverage=leverage,
            type=type, limit_price=limit_price, stop_price=stop_price,
            stop_lose_value=stop_lose_value, stop_lose_kind=stop_lose_kind,
            take_profit_value=take_profit_value, take_profit_kind=take_profit_kind,
            use_trail_stop=use_trail_stop, auto_margin_call=auto_margin_call,
            use_token_for_commission=use_token_for_commission
        )

        _ts = time.time()
        while self.api.buy_order_id == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for buy_order_id')
                break
            pass
        check, data = self.get_order(self.api.buy_order_id)
        while data["status"] == "pending_new":
            time.sleep(0.05)
            check, data = self.get_order(self.api.buy_order_id)
            time.sleep(1)

        if check:
            if data["status"] != "rejected":
                return True, self.api.buy_order_id
            else:
                return False, data["reject_status"]
        else:

            return False, None

    def change_auto_margin_call(self, ID_Name, ID, auto_margin_call):
        self.api.auto_margin_call_changed_respond = None
        self.api.change_auto_margin_call(ID_Name, ID, auto_margin_call)
        _ts = time.time()
        while self.api.auto_margin_call_changed_respond == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for auto_margin_call_changed_respond')
                break
            pass
        if self.api.auto_margin_call_changed_respond["status"] == 2000:
            return True, self.api.auto_margin_call_changed_respond
        else:
            return False, self.api.auto_margin_call_changed_respond

    def change_order(self, ID_Name, order_id,
                     stop_lose_kind, stop_lose_value,
                     take_profit_kind, take_profit_value,
                     use_trail_stop, auto_margin_call):
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
            _ts = time.time()
            while self.api.tpsl_changed_respond == None:
                time.sleep(0.05)
                if time.time() - _ts >= 15:
                    get_logger(__name__).warning('Timeout (15s) waiting for tpsl_changed_respond')
                    break
                pass
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
        self.api.order_data = None
        if hasattr(self.api, 'order_data_event'):
            self.api.order_data_event.clear()
            
        self.api.get_order(buy_order_id)
        
        if hasattr(self.api, 'order_data_event'):
            is_ready = self.api.order_data_event.wait(timeout=30)
            if not is_ready:
                get_logger(__name__).error("Timeout waiting for get_order.")
                return False, None
                
        if self.api.order_data and self.api.order_data.get("status") == 2000:
            return True, self.api.order_data["msg"]
        else:
            return False, None

    def get_pending(self, instrument_type):
        self.api.deferred_orders = None
        self.api.get_pending(instrument_type)
        _ts = time.time()
        while self.api.deferred_orders == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for deferred_orders')
                break
            pass
        if self.api.deferred_orders["status"] == 2000:
            return True, self.api.deferred_orders["msg"]
        else:
            return False, None

    # this function is heavy
    def get_positions(self, instrument_type):
        self.api.positions = None
        if hasattr(self.api, 'positions_event'):
            self.api.positions_event.clear()
            
        self.api.get_positions(instrument_type)
        
        if hasattr(self.api, 'positions_event'):
            is_ready = self.api.positions_event.wait(timeout=30)
            if not is_ready:
                get_logger(__name__).error("Timeout waiting for get_positions.")
                return False, None
                
        if self.api.positions and self.api.positions.get("status") == 2000:
            return True, self.api.positions["msg"]
        else:
            return False, None

    def get_position(self, buy_order_id):
        self.api.position = None
        check, order_data = self.get_order(buy_order_id)
        position_id = order_data["position_id"]
        self.api.get_position(position_id)
        _ts = time.time()
        while self.api.position == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for position')
                break
            pass
        if self.api.position["status"] == 2000:
            return True, self.api.position["msg"]
        else:
            return False, None

    # this function is heavy

    def get_digital_position_by_position_id(self, position_id):
        self.api.position = None
        self.api.get_digital_position(position_id)
        _ts = time.time()
        while self.api.position == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for position')
                break
            pass
        return self.api.position

    def get_digital_position(self, order_id):
        self.api.position = None
        while self.get_async_order(order_id)["position-changed"] == {}:
            time.sleep(0.05)
            pass
        position_id = self.get_async_order(
            order_id)["position-changed"]["msg"]["external_id"]
        self.api.get_digital_position(position_id)
        _ts = time.time()
        while self.api.position == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for position')
                break
            pass
        return self.api.position

    def get_position_history(self, instrument_type):
        self.api.position_history = None
        self.api.get_position_history(instrument_type)
        _ts = time.time()
        while self.api.position_history == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for position_history')
                break
            pass

        if self.api.position_history["status"] == 2000:
            return True, self.api.position_history["msg"]
        else:
            return False, None

    def get_position_history_v2(self, instrument_type, limit, offset, start, end):
        # instrument_type=crypto forex fx-option multi-option cfd digital-option turbo-option
        self.api.position_history_v2 = None
        self.api.get_position_history_v2(
            instrument_type, limit, offset, start, end)
        _ts = time.time()
        while self.api.position_history_v2 == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for position_history_v2')
                break
            pass

        if self.api.position_history_v2["status"] == 2000:
            return True, self.api.position_history_v2["msg"]
        else:
            return False, None

    def get_available_leverages(self, instrument_type, actives=""):
        self.api.available_leverages = None
        if actives == "":
            self.api.get_available_leverages(instrument_type, "")
        else:
            self.api.get_available_leverages(
                instrument_type, OP_code.ACTIVES[actives])
        _ts = time.time()
        while self.api.available_leverages == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for available_leverages')
                break
            pass
        if self.api.available_leverages["status"] == 2000:
            return True, self.api.available_leverages["msg"]
        else:
            return False, None

    def cancel_order(self, buy_order_id):
        self.api.order_canceled = None
        self.api.cancel_order(buy_order_id)
        _ts = time.time()
        while self.api.order_canceled == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for order_canceled')
                break
            pass
        if self.api.order_canceled["status"] == 2000:
            return True
        else:
            return False

    def close_position(self, position_id):
        check, data = self.get_order(position_id)
        if data["position_id"] != None:
            self.api.close_position_data = None
            self.api.close_position(data["position_id"])
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
        else:
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
        self.api.overnight_fee = None
        self.api.get_overnight_fee(instrument_type, OP_code.ACTIVES[active])
        _ts = time.time()
        while self.api.overnight_fee == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for overnight_fee')
                break
            pass
        if self.api.overnight_fee["status"] == 2000:
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
        """
        self.api.live_deal_data[name][active][_type]=deque(list(),buffersize)


        while len(self.api.live_deal_data[name][active][_type])==0:
            time.sleep(0.05)
            self.api.Subscribe_Live_Deal(name,active_id,_type)
            time.sleep(1)
        """

    def unscribe_live_deal(self, name, active, _type):
        active_id = OP_code.ACTIVES[active]
        self.api.Unscribe_Live_Deal(name, active_id, _type)
        """

        while len(self.api.live_deal_data[name][active][_type])!=0:
            time.sleep(0.05)
            self.api.Unscribe_Live_Deal(name,active_id,_type)
            del self.api.live_deal_data[name][active][_type]
            time.sleep(1)
        """

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
        self.api.user_profile_client = None
        self.api.Get_User_Profile_Client(user_id)
        _ts = time.time()
        while self.api.user_profile_client == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for user_profile_client')
                break
            pass

        return self.api.user_profile_client

    def request_leaderboard_userinfo_deals_client(self, user_id, country_id):
        self.api.leaderboard_userinfo_deals_client = None

        while True:
            time.sleep(0.05)
            if self.api.leaderboard_userinfo_deals_client.get("isSuccessful") == True:
                    break
            self.api.Request_Leaderboard_Userinfo_Deals_Client(
                user_id, country_id)
            time.sleep(0.2)

        return self.api.leaderboard_userinfo_deals_client

    def get_users_availability(self, user_id):
        self.api.users_availability = None

        _ts = time.time()
        while self.api.users_availability == None:
            time.sleep(0.05)
            if time.time() - _ts >= 15:
                get_logger(__name__).warning('Timeout (15s) waiting for users_availability')
                break
            self.api.Get_Users_Availability(user_id)
            time.sleep(0.2)
        return self.api.users_availability

    def get_digital_payout(self, active, seconds=0):
        self.api.digital_payout = None
        asset_id = OP_code.ACTIVES[active]

        self.api.subscribe_digital_price_splitter(asset_id)

        start = time.time()
        while self.api.digital_payout is None:
            time.sleep(0.05)
            if seconds and int(time.time() - start) > seconds:
                break

        self.api.unsubscribe_digital_price_splitter(asset_id)

        return self.api.digital_payout if self.api.digital_payout else 0

    def logout(self):
        self.api.logout()

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

        while self.api.digital_option_placed_id.get(request_id) is None:
            time.sleep(0.05)
            pass

        digital_order_id = self.api.digital_option_placed_id.get(request_id)
        if isinstance(digital_order_id, int):
            return True, digital_order_id
        else:
            return False, digital_order_id
