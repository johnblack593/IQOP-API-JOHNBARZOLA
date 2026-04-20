"""Module for IQ option websocket."""

def instruments(api, message):
    if message["name"] == "instruments":
            api.instruments = message["msg"]
            if hasattr(api, 'instruments_event'):
                api.instruments_event.set()
