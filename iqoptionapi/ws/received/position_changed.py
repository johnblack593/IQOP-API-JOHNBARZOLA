"""Module for IQ option websocket."""

def position_changed(api, message):
    if message["name"] == "position-changed":
        order_id = None
        if message["microserviceName"] == "portfolio" and (message["msg"]["source"] == "digital-options") or message["msg"]["source"] == "trading":
            order_id = int(message["msg"]["raw_event"]["order_ids"][0])
            api.order_async[order_id][message["name"]] = message
        elif message["microserviceName"] == "portfolio" and message["msg"]["source"] == "binary-options":
            order_id = int(message["msg"]["external_id"])
            api.order_async[order_id][message["name"]] = message
        else:
            api.position_changed = message
        
        ev = getattr(api, "position_changed_event", None)
        if ev: ev.set()

        # S1-T4: Notify per-order event store for non-blocking check_win_digital()
        if order_id and hasattr(api, 'position_changed_event_store'):
            api.position_changed_event_store[order_id].set()
