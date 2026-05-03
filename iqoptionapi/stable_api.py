
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
from iqoptionapi.core.ratelimit import TokenBucket, rate_limited
from iqoptionapi.http.session import close_shared_session, CHROME_HEADERS
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

    def __init__(self, email, password, active_account_type='PRACTICE'):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self._stop_event = threading.Event()
        from iqoptionapi.candle_cache import CandleCache
        self.candle_cache = CandleCache()
        self._start_maintenance_thread()
        from iqoptionapi.trade_journal import TradeJournal
        self.trade_journal = TradeJournal(journal_dir=getattr(config, 'JOURNAL_DIR', './journal'))
        from iqoptionapi.circuit_breaker import CircuitBreaker
        self.circuit_breaker = CircuitBreaker(max_consecutive_losses=getattr(config, 'CB_MAX_CONSECUTIVE_LOSSES', 3), max_session_loss_usd=getattr(config, 'CB_MAX_SESSION_LOSS_USD', 10.0), max_drawdown_pct=getattr(config, 'CB_MAX_DRAWDOWN_PCT', 0.1), recovery_wait_secs=getattr(config, 'CB_RECOVERY_WAIT_SECS', 300.0))
        from iqoptionapi.martingale_guard import MartingaleGuard, MoneyManagement
        mm_strat = MoneyManagement.FLAT
        try:
            mm_strat = MoneyManagement(getattr(config, 'MM_DEFAULT_STRATEGY', 'flat'))
        except:
            pass
        self.martingale_guard = MartingaleGuard(strategy=mm_strat, base_amount=getattr(config, 'MM_BASE_AMOUNT', 1.0), max_steps=getattr(config, 'MM_MAX_STEPS', 4), max_amount_usd=getattr(config, 'MM_MAX_AMOUNT_USD', 50.0), max_balance_pct=getattr(config, 'MM_MAX_BALANCE_PCT', 0.05))
        from iqoptionapi.strategy.signal_consensus import SignalConsensus
        self.signal_consensus = SignalConsensus(strategies=[])
        from iqoptionapi.validator import Validator
        self.validator = Validator(config)
        from iqoptionapi.session_scheduler import SessionScheduler
        self.session_scheduler = SessionScheduler()
        from iqoptionapi.performance import PerformanceTracker
        self.performance = PerformanceTracker(self.trade_journal)
        from iqoptionapi.reconciler import Reconciler
        self._reconciler = Reconciler(self)
        from iqoptionapi.strategy.market_quality import MarketQualityMonitor
        self.market_quality = MarketQualityMonitor(self.candle_cache)
        from iqoptionapi.strategy.pattern_engine import PatternEngine
        self.pattern_engine = PatternEngine(self.candle_cache)
        from iqoptionapi.strategy.market_regime import MarketRegime
        self.market_regime = MarketRegime(self.candle_cache)
        from iqoptionapi.strategy.correlation_engine import CorrelationEngine
        self.correlation_engine = CorrelationEngine(self.candle_cache)
        from iqoptionapi.asset_scanner import AssetScanner
        self.asset_scanner = AssetScanner(self)
        from iqoptionapi.subscription_manager import SubscriptionManager
        self.subscription_manager = SubscriptionManager(self)
        self.size = [1, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600, 7200, 14400, 28800, 43200, 86400, 604800, 2592000]
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
        self.get_digital_spot_profit_after_sale_data = nested_dict(2, int)
        self.get_realtime_strike_list_temp_data = {}
        self.get_realtime_strike_list_temp_expiration = 0
        self.SESSION_HEADER = CHROME_HEADERS
        self.SESSION_COOKIE = {}
        self.positions_state_data = {}
        self.pending_orders_data = {}
        if hasattr(self, '__init_management__'):
            self.__init_management__()

    def get_server_timestamp(self):
        return self.api.timesync.server_timestamp

    def re_subscribe_stream(self):
        if hasattr(self, 'subscription_manager'):
            for ac in self.subscribe_candle:
                sp = ac.split(',')
                active = sp[0]
                size = int(sp[1])
                self.subscription_manager.subscribe_candle(active, size)
            for ac in self.subscribe_candle_all_size:
                self.subscription_manager.subscribe_candle(ac, "all")
            for ac in self.subscribe_mood:
                self.start_mood_stream(ac)
        else:
            for ac in self.subscribe_candle:
                sp = ac.split(',')
                self.subscribe_candles(sp[0], sp[1])
            for ac in self.subscribe_candle_all_size:
                self.subscribe_candles(ac, "all")
            for ac in self.subscribe_mood:
                self.start_mood_stream(ac)

    def set_session(self, header, cookie):
        self.SESSION_HEADER = header
        self.SESSION_COOKIE = cookie

    def close(self):
        'Gracefully close WebSocket and HTTP session.'
        self._stop_heartbeat_watchdog()
        try:
            self.api.close()
        except Exception:
            pass
        close_shared_session()
        get_logger(__name__).info('IQ_Option instance closed cleanly.')

    def connect(self, sms_code=None, ssid=None):
        if ssid:
            self.ssid = ssid
        if (hasattr(self, 'api') and hasattr(self.api, 'websocket_client')):
            try:
                self.api.close()
            except Exception:
                pass
        self.api = IQOptionAPI('ws.iqoption.com', self.email)
        
        # S15-T4: Auto-debug if requested
        if getattr(config, 'WS_DEBUG_AUTO', False):
            try:
                self.api._ws_debug_file = open("ws_debug.log", "a", encoding="utf-8", buffering=1)
                self.api._ws_debug_logger = True
                self.api._connect_time = time.time()
            except Exception: pass
        if (hasattr(self, 'ssid') and self.ssid):
            self.api.SSID = self.ssid
        self.api.socket_option_closed_event = defaultdict(threading.Event)
        self.api.result_event_store = defaultdict(threading.Event)
        self.api.position_changed_event_store = defaultdict(threading.Event)
        
        # SPRINT 14: Inicializar result_stores si no existen
        if not hasattr(self.api, "digital_option_closed"):
            self.api.digital_option_closed = defaultdict(lambda: None)
        if not hasattr(self.api, "game_betinfo"):
            self.api.game_betinfo = defaultdict(dict)
        check = None
        if (sms_code is not None):
            self.api.setTokenSMS(self.resp_sms)
            (status, reason) = self.api.connect2fa(sms_code)
            if (not status):
                return (status, reason)
        self.api.set_session(headers=self.SESSION_HEADER, cookies=self.SESSION_COOKIE)
        from iqoptionapi.ip_rotation import connect_with_rotation

        def _do_connect():
            return self.api.connect(self._credential_store.consume())
        (check, reason) = connect_with_rotation(_do_connect, max_attempts=3, rotate_on_fail=True)
        if check:
            self._credentials = (self.email, self._credential_store._password)
            self.api._reconnect_callback = self._auto_reconnect
            self.api._heartbeat_callback = (lambda : setattr(self, '_last_heartbeat', __import__('time').time()))
            self._reconnect_manager.reset()
            self._idempotency.purge_expired()
        if (check == True):
            import random
            time.sleep(random.uniform((config.STEALTH_POST_AUTH_DELAY * 0.8), (config.STEALTH_POST_AUTH_DELAY * 1.2)))
            if hasattr(self.api, '_instruments_by_category'):
                self.api._instruments_by_category.clear()
            self.api.instruments = {'instruments': []}
            self.re_subscribe_stream()
            if (self.api.balance_id == None):
                self.api.balance_id_event.wait(timeout=10)
            self.position_change_all('subscribeMessage', self.api.balance_id)
            self.order_changed_all('subscribeMessage')
            self.api.setOptions(1, True)
            try:
                self.update_ACTIVES_OPCODE()
                get_logger(__name__).info('Live Asset Catalogs (Binary, Crypto, Forex, CFD) successfully synchronized.')
            except Exception as e:
                get_logger(__name__).warning('Failed to auto-update asset catalogs: %s', e)
            init_ready = self._wait_for_init_data(timeout=25.0)
            if (not init_ready):
                get_logger(__name__).warning('connect(): initialization-data no llegó en 25s. get_all_open_time() puede retornar listas vacías.')
            self._start_heartbeat_watchdog()
            self.sync_state_on_connect()
            if getattr(config, 'AUTO_REFRESH_TOKEN', True):
                self._start_token_refresh_worker()
            return (True, None)
        else:
            try:
                reason_dict = json.loads(reason)
                if (reason_dict.get('code') == 'verify'):
                    response = self.api.send_sms_code(reason_dict['token'])
                    if (response.json()['code'] != 'success'):
                        return (False, response.json()['message'])
                    self.resp_sms = response
                    return (False, '2FA')
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
            return (False, reason)

    def connect_2fa(self, sms_code):
        return self.connect(sms_code=sms_code)

    def get_all_ACTIVES_OPCODE(self):
        return OP_code.ACTIVES

    def update_ACTIVES_OPCODE(self):
        self.get_ALL_Binary_ACTIVES_OPCODE()
        self.instruments_input_all_in_ACTIVES()
        dicc = {}
        for lis in sorted(OP_code.ACTIVES.items(), key=operator.itemgetter(1)):
            dicc[lis[0]] = lis[1]
        OP_code.ACTIVES = dicc

    def get_name_by_activeId(self, activeId):
        info = self.get_financial_information(activeId)
        try:
            return info['msg']['data']['active']['name']
        except Exception as e:
            return None

    def get_financial_information(self, activeId):
        self.api.financial_information = None
        if hasattr(self.api, 'financial_information_event'):
            self.api.financial_information_event.clear()
        self.api.get_financial_information(activeId)
        if hasattr(self.api, 'financial_information_event'):
            is_ready = self.api.financial_information_event.wait(timeout=30)
            if (not is_ready):
                get_logger(__name__).error('Timeout waiting for financial information.')
                return None
        return self.api.financial_information

    def get_leader_board(self, country, from_position, to_position, near_traders_count, user_country_id=0, near_traders_country_count=0, top_country_count=0, top_count=0, top_type=2):
        self.api.leaderboard_deals_client = None
        country_id = Country.ID[country]
        self.api.leaderboard_deals_client_event.clear()
        self.api.Get_Leader_Board(country_id, user_country_id, from_position, to_position, near_traders_country_count, near_traders_count, top_country_count, top_count, top_type)
        is_ready = self.api.leaderboard_deals_client_event.wait(timeout=15)
        if (not is_ready):
            get_logger(__name__).warning('Timeout (15s) waiting for leaderboard_deals_client')
        return self.api.leaderboard_deals_client

    def get_instruments(self, type):
        '\n        Obtiene instrumentos por tipo ("crypto"/"forex"/"cfd").\n        Intenta WS primero; si retorna lista vacía, hace fallback\n        a extracción desde initialization-data (transparente).\n        '
        time.sleep(self.suspend)
        self.api.instruments = None
        try:
            if hasattr(self.api, 'instruments_event'):
                self.api.instruments_event.clear()
            self.api.get_instruments(type)
            if hasattr(self.api, 'instruments_event'):
                is_ready = self.api.instruments_event.wait(timeout=10)
                if (not is_ready):
                    get_logger(__name__).warning('WS timeout for instruments type: %s', type)
        except Exception as e:
            get_logger(__name__).error('get_instruments WS error for type=%s: %s', type, e)
        ws_result = getattr(self.api, 'instruments', {'instruments': []})
        ws_instruments = []
        if isinstance(ws_result, dict):
            ws_instruments = ws_result.get('instruments', [])
        if (not ws_instruments):
            get_logger(__name__).info('WS returned empty for type=%s, attempting init-data fallback', type)
            try:
                from iqoptionapi.http.instruments import _extract_instruments_from_init
                init_data = getattr(self.api, 'api_option_init_all_result_v2', None)
                if (init_data and isinstance(init_data, dict)):
                    instruments = _extract_instruments_from_init(init_data, type)
                    if instruments:
                        get_logger(__name__).info('Init-data fallback (v2 cache): %d instruments for type=%s', len(instruments), type)
                        return {'instruments': instruments}
                init_data_v1 = getattr(self.api, 'api_option_init_all_result', None)
                if (init_data_v1 and isinstance(init_data_v1, dict)):
                    result_data = init_data_v1.get('result', init_data_v1)
                    instruments = _extract_instruments_from_init(result_data, type)
                    if instruments:
                        get_logger(__name__).info('Init-data fallback (v1 cache): %d instruments for type=%s', len(instruments), type)
                        return {'instruments': instruments}
                get_logger(__name__).info('No cached init data, fetching fresh for type=%s', type)
                fresh_init = self.get_all_init_v2()
                if (fresh_init and isinstance(fresh_init, dict)):
                    instruments = _extract_instruments_from_init(fresh_init, type)
                    if instruments:
                        get_logger(__name__).info('Init-data fallback (fresh): %d instruments for type=%s', len(instruments), type)
                        return {'instruments': instruments}
            except Exception as e:
                get_logger(__name__).error('Init-data fallback failed for type=%s: %s', type, e)
        return (ws_result if ws_instruments else {'instruments': []})

    def instruments_input_to_ACTIVES(self, type):
        instruments = self.get_instruments(type)
        if (instruments and isinstance(instruments, dict) and ('instruments' in instruments)):
            for ins in instruments['instruments']:
                # safer access to id and active_id
                ins_id = ins.get('id') or ins.get('active_id')
                active_id = ins.get('active_id') or ins.get('id')
                if ins_id:
                    OP_code.ACTIVES[ins_id] = active_id
                
                # Also try to map by name if available
                if 'name' in ins:
                    name = str(ins['name'])
                    if '.' in name:
                        name = name.split('.')[1]
                    OP_code.ACTIVES[name] = active_id

    def instruments_input_all_in_ACTIVES(self):
        self.instruments_input_to_ACTIVES('crypto')
        self.instruments_input_to_ACTIVES('forex')
        self.instruments_input_to_ACTIVES('cfd')

    def get_ALL_Binary_ACTIVES_OPCODE(self):
        init_info = self.get_all_init_v2()
        if ((not init_info) or (not isinstance(init_info, dict))):
            return
        for dirr in ['binary', 'turbo', 'blitz']:
            if (dirr in init_info):
                actives = init_info[dirr].get('actives', {})
                for i in actives:
                    try:
                        name_raw = actives[i].get('name', '')
                        if '.' in name_raw:
                            name = name_raw.split('.')[1]
                            OP_code.ACTIVES[name] = int(i)
                        else:
                            OP_code.ACTIVES[name_raw] = int(i)
                    except Exception:
                        continue

    def get_blitz_instruments(self):
        '\n        Returns the catalog of Blitz instruments extracted from the\n        initialization-data WebSocket message. Structure:\n        { "ASSET_NAME": { "id": int, "ticker": str, "enabled": bool,\n                          "is_suspended": bool, "open": bool,\n                          "expirations": [30, 45, ...] } }\n\n        Blitz instruments are NOT available via get_instruments() —\n        the server rejects type="blitz" with error 4000.\n        '
        blitz = getattr(self.api, 'blitz_instruments', {})
        if (not blitz):
            self.get_all_init_v2()
            blitz = getattr(self.api, 'blitz_instruments', {})
        return blitz

    def get_binary_option_detail(self):
        detail = nested_dict(2, dict)
        init_info = self.get_all_init()
        for actives in init_info['result']['turbo']['actives']:
            name = init_info['result']['turbo']['actives'][actives]['name']
            name = name[(name.index('.') + 1):len(name)]
            detail[name]['turbo'] = init_info['result']['turbo']['actives'][actives]
        for actives in init_info['result']['binary']['actives']:
            name = init_info['result']['binary']['actives'][actives]['name']
            name = name[(name.index('.') + 1):len(name)]
            detail[name]['binary'] = init_info['result']['binary']['actives'][actives]
        return detail

    def get_all_profit(self):
        all_profit = nested_dict(2, dict)
        init_info = self.get_all_init()
        for actives in init_info['result']['turbo']['actives']:
            name = init_info['result']['turbo']['actives'][actives]['name']
            name = name[(name.index('.') + 1):len(name)]
            all_profit[name]['turbo'] = ((100.0 - init_info['result']['turbo']['actives'][actives]['option']['profit']['commission']) / 100.0)
        for actives in init_info['result']['binary']['actives']:
            name = init_info['result']['binary']['actives'][actives]['name']
            name = name[(name.index('.') + 1):len(name)]
            all_profit[name]['binary'] = ((100.0 - init_info['result']['binary']['actives'][actives]['option']['profit']['commission']) / 100.0)
        return all_profit

    def get_profile_ansyc(self):
        resp = self.api.getprofile()
        if (resp and (resp.status_code == 200)):
            data = resp.json()
            if (isinstance(data, dict) and data.get('isSuccessful')):
                p_msg = data.get('result')
            else:
                p_msg = data
            if (p_msg and ('balances' in p_msg) and p_msg['balances']):
                self.api.profile.msg = p_msg
                if hasattr(self.api, 'profile_msg_event'):
                    self.api.profile_msg_event.set()
        if ((self.api.profile.msg is None) or ('balances' not in self.api.profile.msg)):
            get_logger(__name__).info('HTTP profile missing balances, waiting for WS profile...')
            is_ready = self.api.profile_msg_event.wait(timeout=config.TIMEOUT_WS_DATA)
            if (not is_ready):
                get_logger(__name__).warning('Timeout waiting for profile via WS')
        return self.api.profile.msg

    def get_currency(self):
        balances_raw = self.get_balances()
        if (balances_raw and ('msg' in balances_raw)):
            for balance in balances_raw['msg']:
                if (balance['id'] == self.api.balance_id):
                    return balance['currency']
        return None

    def get_balance_id(self):
        return self.api.balance_id

    def get_balance(self):
        balances = self.get_balances()
        if balances:
            for balance in balances:
                if (balance['id'] == self.api.balance_id):
                    return balance['amount']
        return 0

    def get_balances(self):
        self.api.balances_raw = None
        if hasattr(self.api, 'balances_raw_event'):
            self.api.balances_raw_event.clear()
        self.api.get_balances()
        if hasattr(self.api, 'balances_raw_event'):
            is_ready = self.api.balances_raw_event.wait(timeout=30)
            if (not is_ready):
                get_logger(__name__).error('Timeout waiting for balances_raw.')
                return None
        return (self.api.balances_raw.get('msg', []) if self.api.balances_raw else [])

    def get_balance_mode(self):
        profile = self.get_profile_ansyc()
        for balance in profile.get('balances'):
            if (balance['id'] == self.api.balance_id):
                if (balance['type'] == 1):
                    return 'REAL'
                elif (balance['type'] == 4):
                    return 'PRACTICE'
                elif (balance['type'] == 2):
                    return 'TOURNAMENT'

    def position_change_all(self, Main_Name, user_balance_id):
        instrument_type = ['cfd', 'forex', 'crypto', 'digital-option', 'turbo-option', 'binary-option']
        for ins in instrument_type:
            self.api.portfolio(Main_Name=Main_Name, name='portfolio.position-changed', instrument_type=ins, user_balance_id=user_balance_id)

    def order_changed_all(self, Main_Name):
        instrument_type = ['cfd', 'forex', 'crypto', 'digital-option', 'turbo-option', 'binary-option']
        for ins in instrument_type:
            self.api.portfolio(Main_Name=Main_Name, name='portfolio.order-changed', instrument_type=ins)

    def stop_candles_stream(self, ACTIVE, size):
        self.unsubscribe_candles(ACTIVE, size)

    def get_all_realtime_candles(self):
        return self.api.real_time_candles

    def full_realtime_get_candle(self, ACTIVE, size, maxdict):
        candles = self.get_candles(ACTIVE, size, maxdict, self.api.timesync.server_timestamp)
        for can in candles:
            self.api.real_time_candles[str(ACTIVE)][int(size)][can['from']] = can

    def subscribe_top_assets_updated(self, instrument_type):
        self.api.Subscribe_Top_Assets_Updated(instrument_type)

    def unsubscribe_top_assets_updated(self, instrument_type):
        self.api.Unsubscribe_Top_Assets_Updated(instrument_type)

    def get_top_assets_updated(self, instrument_type):
        if (instrument_type in self.api.top_assets_updated_data):
            return self.api.top_assets_updated_data[instrument_type]
        else:
            return None

    def subscribe_instruments_realtime(self, instrument_type):
        '\n        Suscribe a la lista de instrumentos en tiempo real para detectar aperturas/cierres.\n        '
        self.subscription_manager.subscribe_instruments_realtime(instrument_type)

    def unsubscribe_instruments_realtime(self, instrument_type):
        '\n        Desuscribe de instrumentos en tiempo real.\n        '
        self.api.unsubscribe_instruments_list(instrument_type)

    def subscribe_commission_changed(self, instrument_type):
        self.api.Subscribe_Commission_Changed(instrument_type)

    def unsubscribe_commission_changed(self, instrument_type):
        self.api.Unsubscribe_Commission_Changed(instrument_type)

    def get_commission_change(self, instrument_type):
        return self.api.subscribe_commission_changed_data[instrument_type]

    def stop_mood_stream(self, ACTIVES, instrument='turbo-option'):
        if (ACTIVES in self.subscribe_mood):
            del self.subscribe_mood[ACTIVES]
        self.api.unsubscribe_Traders_mood(OP_code.ACTIVES[ACTIVES], instrument)

    def get_traders_mood(self, ACTIVES):
        return self.api.traders_mood[OP_code.ACTIVES[ACTIVES]]

    def get_all_traders_mood(self):
        return self.api.traders_mood

    def get_technical_indicators(self, ACTIVES):
        self.api.technical_indicators_event.clear()
        request_id = self.api.get_Technical_indicators(OP_code.ACTIVES[ACTIVES])
        is_ready = self.api.technical_indicators_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning('Timeout waiting for technical_indicators: %s', ACTIVES)
            return None
        return self.api.technical_indicators.get(request_id)

    def _wait_result(self, order_id: (int | str), result_store, event_store: dict, timeout: float=120.0) -> (dict | None):
        'Espera el resultado de un trade sin bloquear el thread forever.\n        \n        Retorna el dict del resultado, o None si vence el timeout.\n        '
        try:
            start_wait = time.time()
            get_logger(__name__).debug('_wait_result: waiting for order_id=%s store=%s', order_id, type(event_store).__name__)
            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                pass
            if hasattr(event_store, 'wait'):
                event = event_store
            elif hasattr(event_store, 'get'):
                event = event_store.get(order_id)
                if (not hasattr(event, 'wait')):
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
            elapsed = (time.time() - start_wait)
            if (not fired):
                get_logger(__name__).debug('_wait_result: timeout for order_id=%s after %.2fs', order_id, elapsed)
                return None
            if hasattr(result_store, 'get_id_data'):
                res = result_store.get_id_data(order_id)
            elif hasattr(result_store, 'get'):
                res = (result_store.get(order_id) if (result_store is not None) else None)
            else:
                try:
                    res = (result_store[order_id] if (result_store is not None) else None)
                except (TypeError, KeyError):
                    res = None
            if ((res is None) and hasattr(self, 'get_async_order')):
                async_data = self.get_async_order(order_id)
                for k in ['position-changed', 'option-closed', 'option']:
                    if (k in async_data):
                        res = async_data.get(k)
                        break
            get_logger(__name__).debug('_wait_result: result=%s elapsed=%.2fs', res, elapsed)
            return res
        except Exception as e:
            get_logger(__name__).warning('_wait_result error for order_id=%s: %s', order_id, e)
            return None
        finally:
            if (not hasattr(event_store, 'wait')):
                try:
                    del event_store[order_id]
                except (KeyError, UnboundLocalError, TypeError):
                    pass

    def get_remaning(self, duration):
        for remaning in get_remaning_time(self.api.timesync.server_timestamp):
            if (remaning[0] == duration):
                return remaning[1]
        get_logger(__name__).error('get_remaning(self,duration) ERROR duration')
        return 'ERROR duration'

    def get_digital_underlying_list_data(self):
        self.api.underlying_list_data = None
        self.api.get_digital_underlying()
        is_ready = self.api.underlying_list_data_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if (not is_ready):
            get_logger(__name__).warning('Timeout waiting for underlying_list_data')
        return self.api.underlying_list_data

    def get_strike_list(self, ACTIVES, duration):
        self.api.strike_list_event.clear()
        self.api.get_strike_list(ACTIVES, duration)
        is_ready = self.api.strike_list_event.wait(timeout=15)
        if (not is_ready):
            get_logger(__name__).warning('Timeout (15s) waiting for strike_list')
            return (None, None)
        ans = {}
        try:
            for data in self.api.strike_list['msg']['strike']:
                temp = {}
                temp['call'] = data['call']['id']
                temp['put'] = data['put']['id']
                ans[('%.6f' % (float(data['value']) * 1e-06))] = temp
        except (KeyError, TypeError) as e:
            get_logger(__name__).error('**error** get_strike_list read problem: %s', e)
            return (self.api.strike_list, None)
        return (self.api.strike_list, ans)




    def get_marginal_balance(self, instrument_type):
        '\n        Obtiene el balance marginal para un tipo de instrumento.\n        '
        if (not hasattr(self.api, 'marginal_balance_event')):
            self.api.marginal_balance_event = threading.Event()
        self.api.marginal_balance_event.clear()
        self.api.get_marginal_balance(instrument_type)
        is_ready = self.api.marginal_balance_event.wait(timeout=10.0)
        if is_ready:
            return self.api.marginal_balance.get(instrument_type)
        return None

    def change_auto_margin_call(self, ID_Name, ID, auto_margin_call):
        self.api.auto_margin_call_changed_respond_event.clear()
        self.api.change_auto_margin_call(ID_Name, ID, auto_margin_call)
        is_ready = self.api.auto_margin_call_changed_respond_event.wait(timeout=15)
        if (not is_ready):
            get_logger(__name__).warning('Timeout (15s) waiting for auto_margin_call_changed_respond')
            return (False, None)
        if (self.api.auto_margin_call_changed_respond['status'] == 2000):
            return (True, self.api.auto_margin_call_changed_respond)
        else:
            return (False, self.api.auto_margin_call_changed_respond)

    def change_order(self, ID_Name, order_id, stop_lose_kind, stop_lose_value, take_profit_kind, take_profit_value, use_trail_stop, auto_margin_call):
        '\n        Changes SL/TP of an existing order or position.\n        \n        Args:\n            stop_lose_kind / take_profit_kind accepted values:\n              "percent"  -> value is percentage (e.g. 50.0 means 50%)\n              "price"    -> value is absolute asset price\n              "pnl"      -> value is amount in USD of profit/loss\n        \n        Example:\n            change_order(..., stop_lose_kind="percent", stop_lose_value=50.0,\n                              take_profit_kind="percent", take_profit_value=100.0)\n        '
        if ((stop_lose_kind is not None) and ((stop_lose_value is None) or (stop_lose_value <= 0))):
            return (False, 'INVALID_PARAMS: stop_lose_value must be > 0 when stop_lose_kind is set')
        if ((take_profit_kind is not None) and ((take_profit_value is None) or (take_profit_value <= 0))):
            return (False, 'INVALID_PARAMS: take_profit_value must be > 0 when take_profit_kind is set')
        if ((stop_lose_kind is None) and (take_profit_kind is None)):
            get_logger(__name__).warning('change_order called with both SL and TP as None')
        check = True
        if (ID_Name == 'position_id'):
            (check, order_data) = self.get_order(order_id)
            position_id = order_data['position_id']
            ID = position_id
        elif (ID_Name == 'order_id'):
            ID = order_id
        else:
            get_logger(__name__).error('change_order input error ID_Name')
        if check:
            self.api.tpsl_changed_respond = None
            self.api.change_order(ID_Name=ID_Name, ID=ID, stop_lose_kind=stop_lose_kind, stop_lose_value=stop_lose_value, take_profit_kind=take_profit_kind, take_profit_value=take_profit_value, use_trail_stop=use_trail_stop)
            self.change_auto_margin_call(ID_Name=ID_Name, ID=ID, auto_margin_call=auto_margin_call)
            self.api.tpsl_changed_respond_event.clear()
            is_ready = self.api.tpsl_changed_respond_event.wait(timeout=15)
            if (not is_ready):
                get_logger(__name__).warning('Timeout (15s) waiting for tpsl_changed_respond')
            if (self.api.tpsl_changed_respond['status'] == 2000):
                return (True, self.api.tpsl_changed_respond['msg'])
            else:
                return (False, self.api.tpsl_changed_respond)
        else:
            get_logger(__name__).error('change_order fail to get position_id')
            return (False, None)

    def get_async_order(self, buy_order_id):
        try:
            buy_order_id = int(buy_order_id)
        except (ValueError, TypeError):
            pass
        return self.api.order_async.get(buy_order_id, {})

    def get_order(self, buy_order_id):
        self.api.order_data_event.clear()
        self.api.get_order(buy_order_id)
        is_ready = self.api.order_data_event.wait(timeout=15)
        if ((not is_ready) or (self.api.order_data is None)):
            get_logger(__name__).warning('Timeout (15s) waiting for order_data')
            return (False, None)
        if (self.api.order_data.get('status') == 2000):
            return (True, self.api.order_data.get('msg'))
        return (True, self.api.order_data)

    def get_pending(self, instrument_type):
        self.api.deferred_orders_event.clear()
        self.api.get_pending(instrument_type)
        is_ready = self.api.deferred_orders_event.wait(timeout=15)
        if (not is_ready):
            get_logger(__name__).warning('Timeout (15s) waiting for deferred_orders')
            return (False, None)
        if (self.api.deferred_orders.get('status') == 2000):
            return (True, self.api.deferred_orders['msg'])
        else:
            return (False, None)

    def get_option_open_by_other_pc(self):
        return self.api.socket_option_opened

    def del_option_open_by_other_pc(self, id):
        del self.api.socket_option_opened[id]
    _MARGIN_TYPE_MAP = {'forex': 'marginal-forex', 'cfd': 'marginal-cfd', 'crypto': 'marginal-crypto', 'marginal-forex': 'marginal-forex', 'marginal-cfd': 'marginal-cfd', 'marginal-crypto': 'marginal-crypto'}

    def get_min_leverage(self, instrument_type, active_id):
        '\n        Retrieves the minimum required leverage for a specific asset.\n        '
        full_type = self._MARGIN_TYPE_MAP.get(instrument_type.lower(), instrument_type)
        if (not full_type.startswith('marginal-')):
            full_type = f'marginal-{full_type}'
        self.get_open_positions(instrument_type=full_type)
        instrument_data = self._get_instrument_data(full_type, active_id)
        if (not instrument_data):
            return 1
        leverage_profile_id = instrument_data.get('leverage_profile_id')
        if (leverage_profile_id is None):
            return 1
        profile = getattr(self.api, 'dynamic_leverage_profiles', {}).get(leverage_profile_id)
        if profile:
            return profile.get('min_leverage', 1)
        return 1

    def _get_instrument_data(self, instrument_type, active_id):
        '\n        Helper to find instrument details in the stored metadata.\n        '
        if ((not hasattr(self.api, 'instruments')) or (not self.api.instruments)):
            return None
        items = self.api.instruments.get('instruments', [])
        for item in items:
            if (item.get('active_id') == active_id):
                return item
        return None

    def opcode_to_name(self, opcode):
        return list(OP_code.ACTIVES.keys())[list(OP_code.ACTIVES.values()).index(opcode)]

    def unscribe_live_deal(self, name, active, _type):
        get_logger(__name__).warning('unscribe_live_deal() is deprecated, use unsubscribe_live_deal()')
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
        self.api.live_deal_data[name][active][_type] = deque(list(), buffersize)

    def get_user_profile_client(self, user_id):
        self.api.user_profile_client_event.clear()
        self.api.Get_User_Profile_Client(user_id)
        is_ready = self.api.user_profile_client_event.wait(timeout=15)
        if (not is_ready):
            get_logger(__name__).warning('Timeout (15s) waiting for user_profile_client')
        return self.api.user_profile_client

    def request_leaderboard_userinfo_deals_client(self, user_id, country_id):
        self.api.leaderboard_userinfo_deals_client_event.clear()
        self.api.Request_Leaderboard_Userinfo_Deals_Client(user_id, country_id)
        is_ready = self.api.leaderboard_userinfo_deals_client_event.wait(timeout=15)
        if (not is_ready):
            get_logger(__name__).warning('Timeout (15s) waiting for leaderboard_userinfo')
        return self.api.leaderboard_userinfo_deals_client

    def get_users_availability(self, user_id):
        self.api.users_availability_event.clear()
        self.api.Get_Users_Availability(user_id)
        is_ready = self.api.users_availability_event.wait(timeout=15)
        if (not is_ready):
            get_logger(__name__).warning('Timeout (15s) waiting for users_availability')
        return self.api.users_availability

    def get_digital_payout(self, active, seconds=0):
        asset_id = OP_code.ACTIVES[active]
        if (hasattr(self.api, 'trading_params_data') and (asset_id in self.api.trading_params_data)):
            data = self.api.trading_params_data[asset_id]
            if ((time.time() - data.get('updated_at', 0)) < 60):
                payout = data.get('payout')
                if payout:
                    return int(payout)
        self.api.digital_payout = None
        self.api.subscribe_digital_price_splitter(asset_id)
        is_ready = self.api.digital_payout_event.wait(timeout=(seconds or config.TIMEOUT_WS_DATA))
        if (not is_ready):
            get_logger(__name__).warning('Timeout waiting for digital_payout')
        try:
            self.api.unsubscribe_digital_price_splitter(asset_id)
        except Exception:
            pass
        return (self.api.digital_payout if self.api.digital_payout else 0)

    def get_payout(self, active):
        '\n        SPRINT 6: Retorna payout de un activo (int).\n        Intenta usar trading-params cache, fallback a digital.\n        '
        active_id = None
        if (active in OP_code.ACTIVES):
            active_id = OP_code.ACTIVES[active]
        if (active_id and hasattr(self.api, 'trading_params_data') and (active_id in self.api.trading_params_data)):
            data = self.api.trading_params_data[active_id]
            if ((time.time() - data.get('updated_at', 0)) < 60):
                payout = data.get('payout')
                if payout:
                    return int(payout)
        return self.get_digital_payout(active)

    def logout(self):
        self.api.logout()

    @rate_limited('_order_bucket')
    def reconcile_missed_results(self, since_ts: float) -> dict:
        '\n        Recupera resultados de trades que expiraron durante una desconexión.\n        Llamar SIEMPRE al reconectar si había trades abiertos.\n\n        Args:\n            since_ts: Unix timestamp de inicio del período a reconciliar\n        Returns:\n            {order_id: "win" | "loose" | "equal" | "unknown"}\n        Note:\n            "loose" is the IQ Option server typo — NOT a bug.\n        '
        return self._reconciler.reconcile(since_ts)

    def get_order_status(self, order_id: int, instrument_type: str):
        '\n        Consulta el estado de una orden por ID sin importar su tipo.\n        instrument_type: "binary" | "turbo" | "digital" | "blitz" | "cfd" | "forex" | "crypto"\n\n        Retorna dict con al menos: {id, status, result, invest, close_profit}\n        Retorna None si no se puede obtener el estado.\n        '
        _binary_types = {'binary', 'turbo', 'blitz'}
        _digital_types = {'digital'}
        _cfd_types = {'cfd', 'forex', 'crypto'}
        itype = instrument_type.lower().replace('-option', '').replace('-', '')
        if (itype in _binary_types):
            (success, data) = self.get_betinfo(order_id)
            if (success and data):
                return {'id': order_id, 'type': instrument_type, 'status': ('closed' if data.get('result') else 'open'), 'result': data.get('result'), 'invest': data.get('amount'), 'close_profit': data.get('win_amount'), 'raw': data}
        elif ((itype in _digital_types) or (itype in _cfd_types)):
            order_data = self.get_async_order(order_id)
            if (order_data and order_data.get('position-changed')):
                msg = order_data['position-changed'].get('msg', {})
                return {'id': order_id, 'type': instrument_type, 'status': msg.get('status', 'unknown'), 'result': msg.get('close_reason'), 'invest': msg.get('invest'), 'close_profit': (msg.get('close_profit') or msg.get('pnl_realized')), 'raw': msg}
        get_logger(__name__).warning('get_order_status: no data found for order_id=%s type=%s', order_id, instrument_type)
        return None

    def _start_maintenance_thread(self):

        def _run():
            while (not self._stop_event.is_set()):
                if self._stop_event.wait(timeout=3600):
                    break
                if hasattr(self, 'candle_cache'):
                    n = self.candle_cache.evict_expired()
                    if (n > 0):
                        get_logger(__name__).info('candle_cache: evicted %d expired candles', n)
        t = threading.Thread(target=_run, name='candle-maintenance', daemon=True)
        t.start()
