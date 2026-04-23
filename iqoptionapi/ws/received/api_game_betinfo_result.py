"""Module for IQ option websocket."""

def api_game_betinfo_result(api, message):
    if message["name"] == "api_game_betinfo_result":
        msg = message.get("msg", {})
        # ensure defaults
        api.game_betinfo.isSuccessful = msg.get("isSuccessful", True)  
        api.game_betinfo.dict = msg
        
        # S7: Notificación reactiva por order_id
        order_id = msg.get("id") or (msg.get("result", {}).get("id") if isinstance(msg.get("result"), dict) else None)
        
        ev_store = getattr(api, "game_betinfo_event", None)
        if ev_store:
            if isinstance(ev_store, dict): # defaultdict
                if order_id is not None:
                    ev_store[order_id].set()
                else:
                    # Fallback si no hay ID: notificar a todos (poco probable pero seguro)
                    for ev in ev_store.values(): ev.set()
            else:
                ev_store.set()
