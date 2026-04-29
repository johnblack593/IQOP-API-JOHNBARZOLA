from iqoptionapi.core.logger import get_logger
import iqoptionapi.core.constants as OP_code
import time

class StreamsMixin:
    def subscribe_candles(self, active, size):
        """
        SPRINT 7: Suscribe a velas con cache local.
        """
        self.api.subscribe_candles(active, size)
        return True

    def unsubscribe_candles(self, active, size):
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
        self.api.subscribe_candles(OP_code.ACTIVES[active], size)
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
        self.api.subscribe_candles(active, size)

    def unsubscribe_candle_v2(self, active, size):
        key = f"{active}_{size}"
        if hasattr(self.api, '_candle_callbacks'):
            self.api._candle_callbacks.pop(key, None)
        self.api.unsubscribe_candles(active, size)

    def subscribe_strike_list(self, ACTIVE, expiration_period):
        self.api.subscribe_instrument_quotes_generated(ACTIVE, expiration_period)

    def unsubscribe_strike_list(self, ACTIVE, expiration_period):
        if ACTIVE in self.api.instrument_quotes_generated_data:
            del self.api.instrument_quotes_generated_data[ACTIVE]
        self.api.unsubscribe_instrument_quotes_generated(ACTIVE, expiration_period)

    def subscribe_live_deal(self, name, active, _type, buffersize):
        active_id = OP_code.ACTIVES[active]
        self.api.Subscribe_Live_Deal(name, active_id, _type)

    def unsubscribe_live_deal(self, name, active, _type):
        active_id = OP_code.ACTIVES[active]
        self.api.Unscribe_Live_Deal(name, active_id, _type)
