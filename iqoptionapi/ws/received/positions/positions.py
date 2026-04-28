def positions(api, message):
    if message["name"] in ["positions", "positions-state"]:
        api.positions = message
        if hasattr(api, 'positions_event'):
            api.positions_event.set()
