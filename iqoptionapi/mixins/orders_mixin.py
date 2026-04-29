from iqoptionapi.core.logger import get_logger
import iqoptionapi.core.constants as OP_code
import time
import threading
from random import randint
from datetime import datetime, timedelta
from iqoptionapi.core.time_sync import _clock
from iqoptionapi.expiration import get_expiration_time

class OrdersMixin:
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

    def buy_digital_spot(self, active, amount, action, duration):
        return self.buy_digital_spot_v2(active, amount, action, duration)

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
            legacy_date = dt_exp.strftime("%Y%m%d%H%M")
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

    def buy_digital(self, amount, instrument_id):
        self.api.result = None
        self.api.result_event.clear()
        self.api.digital_option(instrument_id, amount)
        
        if self.api.result_event.wait(timeout=10):
            if self.api.result:
                return True, self.api.result
        return False, None

    def buy_blitz(self, active, amount, action, current_price, duration=5):
        active_id = OP_code.ACTIVES.get(active)
        if not active_id:
            raise ValueError(f"Unknown active '{active}'")
        
        self.api.result = None
        self.api.result_event.clear()
        self.api.buy_blitz(active_id, amount, action, current_price, duration)
        
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
            amount=amount,
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

    def sell_option(self, options_ids):
        self.api.sell_option(options_ids)
        self.api.result_event.clear()
        if self.api.result_event.wait(timeout=10):
            return self.api.result
        return False

    def sell_digital_option(self, order_id):
        self.api.result_event.clear()
        self.api.sell_digital_option(order_id)
        if self.api.result_event.wait(timeout=10):
            return self.api.result
        return False

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
