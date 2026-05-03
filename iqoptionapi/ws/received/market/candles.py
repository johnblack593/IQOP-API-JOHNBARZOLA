"""Module for IQ option websocket."""

def candles(api, message):
    if message['name'] == 'candles':
        msg = message.get("msg", {})
        if "candles" in msg:
            api.candles.candles_data = msg["candles"]
            api.candles_is_maxdict = True
            if hasattr(api, 'candles_event'):
                api.candles_event.set()
