"""Module for IQ option websocket."""

def position(api, message):
    if message["name"] == "position":
        api.position = message
        ev = getattr(api, "position_event", None)
        if ev: ev.set()
