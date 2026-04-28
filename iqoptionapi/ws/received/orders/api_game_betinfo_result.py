"""Module for IQ option websocket."""

def api_game_betinfo_result(api, message):
    if message["name"] == "api_game_betinfo_result":
        msg = message.get("msg", {})
        # ensure defaults
        # S7: Almacenamiento reactivo por order_id
        order_id = msg.get("id") or (msg.get("result", {}).get("id") if isinstance(msg.get("result"), dict) else None)
        if order_id:
            api.game_betinfo[order_id] = msg
        
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
