import iqoptionapi.core.constants as OP_code
import time
from iqoptionapi.core.logger import get_logger

class StreamsMixin:
    def subscribe_candles(self, active, size):
        """
        SPRINT 11: Delegar al subscription_manager para emulación de browser.
        """
        if hasattr(self, 'subscription_manager'):
            self.subscription_manager.subscribe_candle(active, size)
            return True
        self.api.subscribe_candles(active, size)
        return True

    def unsubscribe_candles(self, active, size):
        if hasattr(self, 'subscription_manager'):
            self.subscription_manager.unsubscribe_candle(active, size)
            return True
        self.api.unsubscribe_candles(active, size)
        return True

    # --- Métodos migrados de stable_api.py ---

    def get_candles(self, active, size, count, datatime):
        self.api.candles_is_maxdict = False
        self.api.candles_wait_for_first_event = False
        self.api.candles_log_count = count
        self.api.getcandles()(OP_code.ACTIVES[active], size, count, datatime)
        
        start_t = time.time()
        while self.api.candles_is_maxdict is False and time.time() - start_t < 20:
            pass
        if self.api.candles_is_maxdict:
            return self.api.candles.candles_data
        else:
            return None

    def get_realtime_candles(self, active, size):
        # Delegar a subscribe_candles que ya usa el manager
        self.subscribe_candles(OP_code.ACTIVES[active], size)
        start_t = time.time()
        while self.api.candles.get_candle(OP_code.ACTIVES[active], size) is None and time.time() - start_t < 20:
            pass
        return self.api.candles.get_candle(OP_code.ACTIVES[active], size)

    def subscribe_candle_v2(self, active, size, callback=None):
        if callback:
            if not hasattr(self.api, '_candle_callbacks'):
                self.api._candle_callbacks = {}
            key = f"{active}_{size}"
            self.api._candle_callbacks[key] = callback
        self.subscribe_candles(active, size)

    def unsubscribe_candle_v2(self, active, size):
        key = f"{active}_{size}"
        if hasattr(self.api, '_candle_callbacks'):
            self.api._candle_callbacks.pop(key, None)
        self.unsubscribe_candles(active, size)

    def subscribe_strike_list(self, ACTIVE, expiration_period):
        if hasattr(self, 'subscription_manager'):
            # El manager aún no tiene método específico para strike list, 
            # pero podemos usar el genérico o llamarlo directamente si es de baja frecuencia.
            # Por ahora lo dejamos directo pero monitoreado.
            pass
        self.api.subscribe_instrument_quotes_generated(ACTIVE, expiration_period)

    def unsubscribe_strike_list(self, ACTIVE, expiration_period):
        if ACTIVE in self.api.instrument_quotes_generated_data:
            del self.api.instrument_quotes_generated_data[ACTIVE]
        self.api.unsubscribe_instrument_quotes_generated(ACTIVE, expiration_period)

    def subscribe_live_deal(self, name, active, _type, buffersize):
        active_id = OP_code.ACTIVES[active]
        if hasattr(self, 'subscription_manager'):
             # Encolar si es posible (pendiente implementar en manager para live_deal)
             pass
        self.api.Subscribe_Live_Deal(name, active_id, _type)

    def unsubscribe_live_deal(self, name, active, _type):
        active_id = OP_code.ACTIVES[active]
        self.api.Unscribe_Live_Deal(name, active_id, _type)

    def get_instrument_quotes_generated_data(self, ACTIVE, duration):
        start_t = time.time()
        while ((self.api.instrument_quotes_generated_raw_data[ACTIVE][(duration * 60)] == {}) and ((time.time() - start_t) < 15.0)):
            self.api.instrument_quotes_generated_event.wait(timeout=1)
            self.api.instrument_quotes_generated_event.clear()
        return self.api.instrument_quotes_generated_raw_data[ACTIVE][(duration * 60)]

    def get_realtime_strike_list(self, ACTIVE, duration):
        start_t = time.time()
        while ((not self.api.instrument_quotes_generated_data[ACTIVE][(duration * 60)]) and ((time.time() - start_t) < 15.0)):
            self.api.instrument_quotes_generated_event.wait(timeout=1)
            self.api.instrument_quotes_generated_event.clear()
        ans = {}
        now_timestamp = self.api.instrument_quotes_generated_timestamp[ACTIVE][(duration * 60)]
        while (ans == {}):
            if ((self.get_realtime_strike_list_temp_data == {}) or (now_timestamp != self.get_realtime_strike_list_temp_expiration)):
                (raw_data, strike_list) = self.get_strike_list(ACTIVE, duration)
                if raw_data:
                    self.get_realtime_strike_list_temp_expiration = raw_data['msg']['expiration']
                    self.get_realtime_strike_list_temp_data = strike_list
                else:
                    break
            else:
                strike_list = self.get_realtime_strike_list_temp_data
            profit = self.api.instrument_quotes_generated_data[ACTIVE][(duration * 60)]
            for price_key in strike_list:
                try:
                    side_data = {}
                    for side_key in strike_list[price_key]:
                        detail_data = {}
                        profit_d = profit[strike_list[price_key][side_key]]
                        detail_data['profit'] = profit_d
                        detail_data['id'] = strike_list[price_key][side_key]
                        side_data[side_key] = detail_data
                    ans[price_key] = side_data
                except (KeyError, TypeError) as e:
                    get_logger(__name__).error('Data extraction error: %s', e)
            if (ans == {}):
                self.api.instrument_quotes_generated_event.wait(timeout=1)
                self.api.instrument_quotes_generated_event.clear()
        return ans
