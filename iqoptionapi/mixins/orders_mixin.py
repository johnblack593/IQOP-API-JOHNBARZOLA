from iqoptionapi.logger import get_logger
import iqoptionapi.constants as OP_code
import time
from random import randint
from datetime import datetime, timedelta
from iqoptionapi.time_sync import _clock
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
