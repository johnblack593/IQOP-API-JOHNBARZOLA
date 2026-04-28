"""Module for IQ option websocket."""

def history_positions(api, message):
    if message["name"] == "history-positions":
        api.position_history_v2 = message
        ev = getattr(api, "position_history_v2_event", None)
        if ev: ev.set()
