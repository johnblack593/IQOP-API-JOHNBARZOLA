"""Module for IQ option websocket."""

def positions(api, message):
    if message["name"] == "positions":
        api.positions = message
        if hasattr(api, 'positions_event'):
            api.positions_event.set()
