"""Module for IQ option websocket."""

def position_history(api, message):
    if message["name"] == "position-history":
        api.position_history = message
        ev = getattr(api, "position_history_event", None)
        if ev: ev.set()
