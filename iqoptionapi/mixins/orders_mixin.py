from iqoptionapi.core.logger import get_logger
import iqoptionapi.core.constants as OP_code
import time
import threading
from random import randint
from datetime import datetime, timedelta
from iqoptionapi.core.time_sync import _clock
from iqoptionapi.expiration import get_expiration_time
from iqoptionapi.core.ratelimit import rate_limited

class OrdersMixin:
    @rate_limited("_order_bucket", on_limit=(False, None))
    def buy(self, price, ACTIVES, ACTION, expirations):
        # Gate de validación
        if hasattr(self, 'validator') and self.validator is not None:
            is_valid, reason = self.validator.validate_order(
                active=ACTIVES,
                amount=price,
                action=ACTION,
                duration=expirations,
                instrument_type="binary"
            )
            if not is_valid:
                get_logger(__name__).error("buy rejected by validator: %s", reason)
                return False, None

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
        
        # Wait for either result (success=False) or correlated ID (Sprint 3)
        start_t = time.time()
        id = None
        while time.time() - start_t < 15:
            id = self.api.buy_multi_option.get(req_id, {}).get("id")
            if id:
                break
            
            # Si el result llegó y dice success=False, abortamos
            if self.api.buy_multi_option.get(req_id, {}).get("success") == False:
                break
                
            if self.api.result_event.wait(timeout=0.1):
                self.api.result_event.clear()
        
        if id is None:
            get_logger(__name__).warning("buy TIMEOUT or NO ID: req_id=%s", req_id)
            return False, None
        return self.api.result, id

    @rate_limited("_order_bucket", on_limit=(False, None))
    def buy_digital_spot(self, active, amount, action, duration):
        return self.buy_digital_spot_v2(active, amount, action, duration)

    @rate_limited("_order_bucket", on_limit=(False, None))
    def buy_digital_spot_v2(self, active, amount, action, duration):
        # Gate de validación
        if hasattr(self, 'validator') and self.validator is not None:
            is_valid, reason = self.validator.validate_order(
                active=active,
                amount=amount,
                action=action,
                duration=duration,
                instrument_type="digital"
            )
            if not is_valid:
                get_logger(__name__).error("buy_digital_spot_v2 rejected by validator: %s", reason)
                return False, None

        action = action.lower()

        if action == 'put':
            action = 'P'
        elif action == 'call':
            action = 'C'
        else:
            get_logger(__name__).error('buy_digital_spot_v2 active error')
            return -1, None

        # SPRINT 7: Usar reloj sincronizado global
        timestamp = int(_clock.now())

        if duration == 1:
            exp, _ = get_expiration_time(timestamp, duration)
        else:
            now_date = datetime.fromtimestamp(timestamp).replace(second=0, microsecond=0) + \
                       timedelta(minutes=1, seconds=30)

            for _ in range(100):
                if now_date.minute % duration == 0 and time.mktime(now_date.timetuple()) - timestamp > 30:
                    break
                now_date = now_date + timedelta(minutes=1)

            exp = time.mktime(now_date.replace(second=0, microsecond=0).timetuple())

        dt_exp = datetime.utcfromtimestamp(exp)
        date_formated = dt_exp.strftime("%Y%m%d")
        time_formated = dt_exp.strftime("%H%M%S")
        
        active_id = OP_code.ACTIVES.get(active)
        if active_id:
            instrument_id = f"do{active_id}A{date_formated}D{time_formated}PT{duration}M{action}SPT"
        else:
            clean_active = active.replace("-OTC", "")
            legacy_date = dt_exp.strftime("%Y%m%dH%M")
            instrument_id = f"do{clean_active}{legacy_date}PT{duration}M{action}SPT"

        get_logger(__name__).debug("Digital Instrument ID generated: %s", instrument_id)
        
        for attempt in range(2):
            try:
                request_id = self.api.place_digital_option_v2(instrument_id, active_id, amount)
                break
            except Exception as e:
                if attempt == 0:
                    get_logger(__name__).warning("Connection lost before trade, waiting for recovery...")
                    time.sleep(2)
                    if not self.check_connect():
                        ssid = getattr(self, 'ssid', None)
                        self.connect(ssid=ssid)
                else:
                    raise e

        is_ready = self.api.digital_option_placed_id_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).error('Timeout (15s) waiting for digital_option_placed_id')
            return False, None
        digital_order_id = self.api.digital_option_placed_id.get(request_id)
        if isinstance(digital_order_id, int):
            return True, digital_order_id
        else:
            return False, digital_order_id

    @rate_limited("_order_bucket", on_limit=(False, None))
    def buy_digital(self, amount, instrument_id):
        self.api.result = None
        self.api.result_event.clear()
        self.api.digital_option(instrument_id, amount)
        
        if self.api.result_event.wait(timeout=10):
            if self.api.result:
                return True, self.api.result
        return False, None

    @rate_limited("_order_bucket", on_limit=(False, None))
    def buy_blitz(self, active, amount, action, current_price, duration=5):
        active_id = OP_code.ACTIVES.get(active)
        if not active_id:
            raise ValueError(f"Unknown active '{active}'")
        
        self.api.result = None
        self.api.result_event.clear()
        self.api.buy_blitz(active_id, action, amount, current_price, duration)
        
        if self.api.result_event.wait(timeout=10):
            if self.api.result:
                return True, self.api.result
        return False, None

    def place_pending_order(self, active, instrument_type, side, amount, leverage, 
                             stop_price, take_profit=None, stop_loss=None):
        active_id = OP_code.ACTIVES.get(active)
        self.api.result = None
        self.api.result_event.clear()
        
        self.api.place_stop_order(
            active_id=active_id,
            instrument_type=instrument_type,
            side=side,
            margin=amount,
            leverage=leverage,
            stop_price=stop_price,
            take_profit=take_profit,
            stop_loss=stop_loss
        )
        
        if self.api.result_event.wait(timeout=10):
            return True, self.api.result
        return False, "Timeout"

    def create_price_alert(self, active, price, direction):
        active_id = OP_code.ACTIVES.get(active)
        if not active_id:
            raise ValueError(f"Unknown active '{active}'")
        
        self.api.result = None
        self.api.result_event.clear()
        self.api.create_alert(active_id, price, direction)
        
        if self.api.result_event.wait(timeout=10):
            if isinstance(self.api.result, dict) and "id" in self.api.result:
                return True, self.api.result["id"]
            return True, self.api.result
        
        return False, "Timeout"

    def delete_price_alert(self, alert_id):
        """
        SPRINT 8: Elimina una alerta de precio existente.
        """
        get_logger(__name__).info("Deleting price alert: %s", alert_id)
        self.api.result = None
        self.api.result_event.clear()
        self.api.delete_alert(alert_id)
        
        if self.api.result_event.wait(timeout=10):
            return True, self.api.result
            
        return False, "Timeout"

    # --- Métodos migrados de stable_api.py ---
    
    @rate_limited("_order_bucket", on_limit=None)
    def buy_multi(self, price, ACTIVES, ACTION, expirations):
        self.api.buy_multi_option = {}
        if len(price) == len(ACTIVES) == len(ACTION) == len(expirations):
            buy_len = len(price)
            for idx in range(buy_len):
                self.api.buyv3(
                    price[idx], OP_code.ACTIVES[ACTIVES[idx]], ACTION[idx], expirations[idx], idx)
            start_multi_t = time.time()
            while len(self.api.buy_multi_option) < buy_len and time.time() - start_multi_t < 30:
                self.api.result_event.wait(timeout=0.1)
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

    @rate_limited("_order_bucket", on_limit=(False, None))
    def buy_by_raw_expirations(self, price, active, direction, option, expired):
        self.api.buy_multi_option = {}
        self.api.result_event.clear()
        req_id = "raw_exp"
        self.api.buy_multi_option[req_id] = {"id": None}
        self.api.buyv3(float(price), OP_code.ACTIVES[active], str(direction), int(expired), req_id)
        
        start_t = time.time()
        while time.time() - start_t < 30:
            if self.api.buy_multi_option[req_id]["id"] is not None:
                return True, self.api.buy_multi_option[req_id]["id"]
            if self.api.result_event.wait(timeout=0.1):
                self.api.result_event.clear()
        return False, None

    @rate_limited("_order_bucket", on_limit=None)
    def sell_option(self, options_ids):
        self.api.sell_option(options_ids)
        self.api.result_event.clear()
        if self.api.result_event.wait(timeout=10):
            return self.api.result
        return False

    @rate_limited("_order_bucket", on_limit=None)
    def sell_digital_option(self, order_id):
        self.api.result_event.clear()
        self.api.sell_digital_option(order_id)
        if self.api.result_event.wait(timeout=10):
            return self.api.result
        return False

    @rate_limited("_order_bucket", on_limit=(False, None))
    def buy_order(self,
                  instrument_type, instrument_id,
                  side, amount, leverage,
                  type="market", limit_price=None, stop_price=None,
                  stop_lose_kind=None, stop_lose_value=None,
                  take_profit_kind=None, take_profit_value=None,
                  use_trail_stop=False, auto_margin_call=False,
                  use_token_for_commission=False):
        self.api.buy_order_id = None
        self.api.buy_order(
            instrument_type=instrument_type, instrument_id=instrument_id,
            side=side, amount=amount, leverage=leverage,
            type=type, limit_price=limit_price, stop_price=stop_price,
            stop_lose_kind=stop_lose_kind, stop_lose_value=stop_lose_value,
            take_profit_kind=take_profit_kind, take_profit_value=take_profit_value,
            use_trail_stop=use_trail_stop, auto_margin_call=auto_margin_call,
            use_token_for_commission=use_token_for_commission
        )
        start_t = time.time()
        while self.api.buy_order_id is None and time.time() - start_t < 30:
            pass
        if self.api.buy_order_id is not None:
            return True, self.api.buy_order_id
        else:
            return False, None

    def cancel_pending_order(self, order_id):
        self.api.order_canceled_event.clear()
        self.api.cancel_order(order_id)
        is_ready = self.api.order_canceled_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for order_canceled')
            return False
        return self.api.order_canceled.get("status") == 2000

    def get_pending_orders(self, instrument_type):
        self.api.orders_state_event = threading.Event()
        self.api.get_orders_state(instrument_type)
        is_ready = self.api.orders_state_event.wait(timeout=10.0)
        if is_ready:
            return getattr(self.api, "orders_state_data", {})
        return {}

    def cancel_order(self, buy_order_id):
        self.api.order_canceled_event.clear()
        self.api.cancel_order(buy_order_id)
        is_ready = self.api.order_canceled_event.wait(timeout=15)
        if not is_ready:
            get_logger(__name__).warning('Timeout (15s) waiting for order_canceled')
            return False
        return self.api.order_canceled.get("status") == 2000

    def check_binary_order(self, order_id):
        self.api.order_binary_id_event.clear()
        self.api.get_binary_order_id(order_id)
        if self.api.order_binary_id_event.wait(timeout=10):
            return self.api.order_binary_id
        return None

    def check_win(self, id):
        while True:
            try:
                return self.api.socket_option_closed[id]["msg"]["win"]
            except Exception:
                pass

    def check_win_v2(self, id):
        while True:
            if id in self.api.socket_option_closed:
                return self.api.socket_option_closed[id]["msg"]["win"]
            time.sleep(0.1)

    def check_win_v3(self, id):
        start_t = time.time()
        while time.time() - start_t < 60:
            if id in self.api.socket_option_closed:
                return True, self.api.socket_option_closed[id]["msg"]["win"]
            time.sleep(0.1)
        return False, None

    def check_win_v4(self, id):
        # SPRINT 4: Usar evento para evitar spinlock
        if id in self.api.socket_option_closed:
            return True, self.api.socket_option_closed[id]["msg"]["win"]
        
        is_ready = self.api.socket_option_closed_event.wait(timeout=60)
        if is_ready:
            if id in self.api.socket_option_closed:
                return True, self.api.socket_option_closed[id]["msg"]["win"]
        return False, None

    def check_win_digital(self, order_id):
        while True:
            if order_id in self.api.digital_option_closed:
                return self.api.digital_option_closed[order_id]
            time.sleep(0.1)

    def check_win_digital_v2(self, order_id):
        start_t = time.time()
        while time.time() - start_t < 60:
            if order_id in self.api.digital_option_closed:
                return True, self.api.digital_option_closed[order_id]
            time.sleep(0.1)
        return False, None

    def get_betinfo(self, id):
        self.api.game_betinfo.isSuccessful = None
        self.api.game_betinfo.dict = None
        self.api.get_betinfo(id)
        start_t = time.time()
        while self.api.game_betinfo.isSuccessful is None and time.time() - start_t < 30:
            pass
        if self.api.game_betinfo.isSuccessful is None:
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


    def check_cfd_order_capability(self, force=False):
        '\n        Probes whether the server accepts place-order-temp messages.\n        Returns True if CFD/Forex orders are supported, False otherwise.\n        Result is cached after first call.\n        '
        if ((self._cfd_order_capable is not None) and (not force)):
            return self._cfd_order_capable
        get_logger(__name__).info('Probing CFD order capability...')
        _PROBE_CANDIDATES = [('forex', 'EURUSD-OTC'), ('forex', 'USDJPY-OTC'), ('forex', 'GBPUSD-OTC'), ('cfd', 'APPLE-OTC'), ('crypto', 'BTCUSD-OTC')]
        test_asset = None
        test_type = None
        for (cat, name) in _PROBE_CANDIDATES:
            if (name in OP_code.ACTIVES):
                test_asset = name
                test_type = cat
                break
        if (not test_asset):
            for name in OP_code.ACTIVES:
                if ('OTC' in name):
                    test_asset = name
                    test_type = 'forex'
                    break
        if (not test_asset):
            get_logger(__name__).warning('No OTC assets in ACTIVES to probe CFD capability')
            self._cfd_order_capable = False
            return False
        self.api.buy_order_id = None
        try:
            self.api.buy_order(instrument_type=test_type, instrument_id=test_asset, side='buy', amount=1, leverage=1, type='market', limit_price=None, stop_price=None, stop_lose_value=None, stop_lose_kind=None, take_profit_value=None, take_profit_kind=None, use_trail_stop=False, auto_margin_call=False, use_token_for_commission=False)
        except Exception as e:
            get_logger(__name__).warning('CFD probe send failed: %s', e)
            self._cfd_order_capable = False
            return False
        self.api.order_data_event.clear()
        is_ready = self.api.order_data_event.wait(timeout=3)
        if (self.api.buy_order_id is not None):
            get_logger(__name__).info('CFD orders SUPPORTED — probe order_id=%s', self.api.buy_order_id)
            try:
                self.close_position(self.api.buy_order_id)
            except Exception:
                pass
            self._cfd_order_capable = True
        else:
            get_logger(__name__).warning('CFD orders NOT SUPPORTED for this account (server silently dropped place-order-temp)')
            self._cfd_order_capable = False
        return self._cfd_order_capable

    def open_margin_position(self, instrument_type, active_id, direction, amount, leverage, take_profit=None, stop_loss=None, timeout=30.0):
        '\n        Opens a margin position using the modern marginal-{type}.place-market-order protocol.\n\n        Args:\n            instrument_type: "forex", "cfd", or "crypto"\n            active_id: Numeric active ID (e.g., 1 for EURUSD)\n            direction: "buy" or "sell"\n            amount: Amount in USD (the margin)\n            leverage: Leverage multiplier (e.g., 50, 100, 1000)\n            take_profit: dict with "type" and "value", or None\n                         Example: {"type": "pnl", "value": 5}  -> +$5 profit\n                         Example: {"type": "price", "value": 1.17200}\n                         Example: {"type": "percent", "value": 50}\n            stop_loss: dict with "type" and "value", or None\n                       Example: {"type": "pnl", "value": 3}  -> -$3 loss (auto-negated)\n                       Example: {"type": "price", "value": 1.16800}\n            timeout: Max wait time in seconds\n\n        Returns:\n            (True, position_dict) on success\n            (False, error_string) on failure\n        '
        if (amount <= 0):
            return (False, 'INVALID_PARAMS: amount must be > 0')
        if (direction not in ('buy', 'sell')):
            return (False, f"INVALID_PARAMS: invalid direction '{direction}'")
        if (instrument_type.lower() not in self._MARGIN_TYPE_MAP):
            return (False, f"INVALID_PARAMS: unknown instrument_type '{instrument_type}'")
        self.api.margin_order_result = None
        self.api.margin_order_event.clear()
        try:
            self.api.place_margin_order(instrument_type=instrument_type, active_id=active_id, side=direction, margin=amount, leverage=leverage, take_profit=take_profit, stop_loss=stop_loss)
        except Exception as e:
            get_logger(__name__).error('open_margin_position send failed: %s', e)
            return (False, f'SEND_ERROR: {e}')
        is_ready = self.api.margin_order_event.wait(timeout=timeout)
        if (is_ready and (self.api.margin_order_result is not None)):
            order_result = self.api.margin_order_result
            if (order_result.get('id') is not None):
                get_logger(__name__).info('Margin position opened: id=%s type=%s side=%s amount=%s leverage=%s', order_result.get('id'), instrument_type, direction, amount, leverage)
                return (True, order_result)
            else:
                return (False, f"REJECTED: {order_result.get('error', order_result)}")
        else:
            get_logger(__name__).error('open_margin_position TIMEOUT (%.0fs) for %s %s', timeout, instrument_type, direction)
            return (False, f'TIMEOUT after {timeout}s')

    def modify_margin_tp_sl(self, order_id, take_profit=None, stop_loss=None):
        '\n        Modifies TP/SL of an open margin position using the modern protocol.\n        '
        (position_id, m_type) = self._resolve_margin_position_id(order_id)
        results = []
        if (take_profit is not None):
            get_logger(__name__).info('Updating margin TP: pos=%s, val=%s', position_id, take_profit)
            tp_data = {'name': f'marginal-{m_type}.change-position-take-profit-order', 'version': '1.0', 'body': {'position_id': int(position_id), 'level': {'type': str(take_profit.get('type', 'pnl')), 'value': float(take_profit.get('value', 0))}}}
            self.api.result = None
            self.api.result_event.clear()
            self.api.send_websocket_request('sendMessage', tp_data)
            if (not self.api.result_event.wait(timeout=10)):
                get_logger(__name__).warning('Timeout waiting for TP update result')
                results.append(False)
            else:
                results.append(self.api.result)
        if (stop_loss is not None):
            get_logger(__name__).info('Updating margin SL: pos=%s, val=%s', position_id, stop_loss)
            sl_value = float(stop_loss.get('value', 0))
            if ((str(stop_loss.get('type', 'pnl')) == 'pnl') and (sl_value > 0)):
                sl_value = (- abs(sl_value))
            sl_data = {'name': f'marginal-{m_type}.change-position-stop-loss-order', 'version': '2.0', 'body': {'position_id': int(position_id), 'level': {'type': str(stop_loss.get('type', 'pnl')), 'value': sl_value}, 'trailing_stop': bool(stop_loss.get('trailing_stop', False))}}
            self.api.result = None
            self.api.result_event.clear()
            self.api.send_websocket_request('sendMessage', sl_data)
            if (not self.api.result_event.wait(timeout=10)):
                get_logger(__name__).warning('Timeout waiting for SL update result')
                results.append(False)
            else:
                results.append(self.api.result)
        if (not results):
            return (True, 'NO_CHANGES')
        final_success = all(results)
        return (final_success, {'results': results})
