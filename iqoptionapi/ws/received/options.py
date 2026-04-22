"""Module for IQ option websocket."""

def option(api, message):
    if message["name"] == "options":
        api.get_options_v2_data = message
        ev = getattr(api, "get_options_v2_data_event", None)
        if ev: ev.set()
