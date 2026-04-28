from iqoptionapi.logger import get_logger
import iqoptionapi.constants as OP_code
import time

class StreamsMixin:
    def start_candles_stream(self, ACTIVE, size, maxdict):
        if size == "all":
            for s in self.size:
                self.full_realtime_get_candle(ACTIVE, s, maxdict)
                self.api.real_time_candles_maxdict_table[ACTIVE][s] = maxdict
            self.start_candles_all_size_stream(ACTIVE)
        elif size in self.size:
            self.api.real_time_candles_maxdict_table[ACTIVE][size] = maxdict
            self.full_realtime_get_candle(ACTIVE, size, maxdict)
            self.subscription_manager.subscribe_candle(ACTIVE, size)
            
            start_t = time.time()
            while not self.api.candle_generated_check.get(str(ACTIVE), {}).get(int(size)) and (time.time() - start_t < 15.0):
                self.api.candles_event.wait(timeout=1.0)
                self.api.candles_event.clear()
        else:
            get_logger(__name__).error('**error** start_candles_stream please input right size')

    def stop_candles_stream(self, ACTIVE, size):
        if size == "all":
            self.stop_candles_all_size_stream(ACTIVE)
        elif size in self.size:
            self.stop_candles_one_stream(ACTIVE, size)
        else:
            get_logger(__name__).error('**error** start_candles_stream please input right size')

    def get_realtime_candles(self, ACTIVE, size):
        if size == "all":
            try:
                return self.api.real_time_candles[ACTIVE]
            except Exception:
                return False
        elif size in self.size:
            try:
                return self.api.real_time_candles[ACTIVE][size]
            except Exception:
                return False
        return False

    def get_all_realtime_candles(self):
        return self.api.real_time_candles

    def full_realtime_get_candle(self, ACTIVE, size, maxdict):
        candles = self.get_candles(ACTIVE, size, maxdict, self.api.timesync.server_timestamp)
        for can in candles:
            self.api.real_time_candles[str(ACTIVE)][int(size)][can["from"]] = can

    def start_candles_one_stream(self, ACTIVE, size):
        if not (ACTIVE in self.api.real_time_candles and size in self.api.real_time_candles[ACTIVE]):
            self.subscription_manager.subscribe_candle(ACTIVE, size)
            
        start_t = time.time()
        while not self.api.candle_generated_check.get(str(ACTIVE), {}).get(int(size)) and (time.time() - start_t < 20.0):
            self.api.candles_event.wait(timeout=1.0)
            self.api.candles_event.clear()
            
        return self.api.candle_generated_check.get(str(ACTIVE), {}).get(int(size)) == True

    def stop_candles_one_stream(self, ACTIVE, size):
        if ((ACTIVE + "," + str(size)) in self.subscribe_candle):
            self.subscribe_candle.remove(ACTIVE + "," + str(size))
        
        self.api.candle_generated_check[str(ACTIVE)][int(size)] = {}
        self.api.unsubscribe(OP_code.ACTIVES[ACTIVE], size)
        
        start_t = time.time()
        while self.api.candle_generated_check.get(str(ACTIVE), {}).get(int(size)) != {} and (time.time() - start_t < 20.0):
            time.sleep(0.1)
        return True

    def start_candles_all_size_stream(self, ACTIVE):
        self.api.candle_generated_all_size_check[str(ACTIVE)] = {}
        if (str(ACTIVE) in self.subscribe_candle_all_size) == False:
            self.subscribe_candle_all_size.append(str(ACTIVE))
        
        self.api.subscribe_all_size(OP_code.ACTIVES[ACTIVE])
        start_t = time.time()
        while not self.api.candle_generated_all_size_check.get(str(ACTIVE)) and (time.time() - start_t < 20.0):
            self.api.candles_event.wait(timeout=1.0)
            self.api.candles_event.clear()
            
        return self.api.candle_generated_all_size_check.get(str(ACTIVE)) == True

    def stop_candles_all_size_stream(self, ACTIVE):
        if (str(ACTIVE) in self.subscribe_candle_all_size):
            self.subscribe_candle_all_size.remove(str(ACTIVE))
        
        self.api.candle_generated_all_size_check[str(ACTIVE)] = {}
        self.api.unsubscribe_all_size(OP_code.ACTIVES[ACTIVE])
        
        start_t = time.time()
        while self.api.candle_generated_all_size_check.get(str(ACTIVE)) != {} and (time.time() - start_t < 10.0):
            time.sleep(0.1)
        return True

    def start_mood_stream(self, ACTIVES, instrument="turbo-option"):
        self.api.subscribe_mood(ACTIVES, instrument)

    def get_short_active_info(self, active_id, timeout=5.0):
        import threading
        if not hasattr(self.api, "short_active_info_event"):
             self.api.short_active_info_event = threading.Event()
        self.api.short_active_info_event.clear()
        self.api.subscribe_short_active_info(active_id)
        if self.api.short_active_info_event.wait(timeout=timeout):
            return self.api.short_active_info_data.get(active_id)
        return None

    def get_exchange_rate(self, from_currency, to_currency, timeout=5.0):
        import threading
        pair = f"{from_currency}/{to_currency}"
        if not hasattr(self.api, "exchange_rate_event"):
            self.api.exchange_rate_event = threading.Event()
        if self.api.exchange_rate_event.wait(timeout=timeout):
            return self.api.exchange_rates.get(pair)
        return None
