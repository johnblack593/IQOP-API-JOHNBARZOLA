"""Module for IQ option websocket."""

def api_game_getoptions_result(api, message):
    if message["name"] == "api_game_getoptions_result":
        api.api_game_getoptions_result = message
        ev = getattr(api, "api_game_getoptions_result_event", None)
        if ev: ev.set()
