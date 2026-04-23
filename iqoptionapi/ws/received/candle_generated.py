"""Module for IQ option websocket."""
import iqoptionapi.constants as OP_code

def candle_generated_realtime(api, message, dict_queue_add):
    if message["name"] == "candle-generated":
        Active_name = list(OP_code.ACTIVES.keys())[list(
            OP_code.ACTIVES.values()).index(message["msg"]["active_id"])]

        active = str(Active_name)
        size = int(message["msg"]["size"])
        from_ = int(message["msg"]["from"])
        msg = message["msg"]
        maxdict = api.real_time_candles_maxdict_table[Active_name][size]

        dict_queue_add(api.real_time_candles,
                            maxdict, active, size, from_, msg)
        
        # S3-T1: Integration with CandleCache
        if hasattr(api, 'candle_cache'):
            api.candle_cache.add_candle(message["msg"]["active_id"], size, msg)

        # S3-T3: Fire dynamic callbacks
        key = (message["msg"]["active_id"], size)
        cb = getattr(api, '_candle_callbacks', {}).get(key)
        if cb is not None:
            try:
                cb(msg)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("on_candle callback error: %s", e)

        api.candle_generated_check[active][size] = True
