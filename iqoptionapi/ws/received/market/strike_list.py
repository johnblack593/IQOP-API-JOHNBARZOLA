"""Module for IQ option websocket."""

def strike_list(api, message):
    if message["name"] == "strike-list":
        api.strike_list = message
        ev = getattr(api, "strike_list_event", None)
        if ev: ev.set()
