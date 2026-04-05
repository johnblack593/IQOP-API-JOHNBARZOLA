"""Module for IQ option websocket."""

def api_game_betinfo_result(api, message):
    if message["name"] == "api_game_betinfo_result":
        msg = message.get("msg", {})
        # ensure defaults
        api.game_betinfo.isSuccessful = msg.get("isSuccessful", True)  
        api.game_betinfo.dict = msg
        
        if hasattr(api, "game_betinfo_event"):
            api.game_betinfo_event.set()
