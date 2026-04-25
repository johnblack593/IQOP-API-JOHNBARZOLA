"""Module for IQ option websocket."""

def order_placed_temp(api, message):
    if message["name"] == "order-placed-temp":
        msg_body = message.get("msg", {})
        # S5-T3: Debugging structure
        print(f"DEBUG_ORDER_PLACED_TEMP: {list(msg_body.keys())}")
        if "id" not in msg_body and "order_id" not in msg_body:
            print(f"DEBUG_ORDER_PLACED_TEMP_FULL: {msg_body}")

        # S5-T3: Fallback for order_id if id is missing
        api.buy_order_id = msg_body.get("id") or msg_body.get("order_id")
        
        # S5-T3: Notificar evento para evitar bloqueos
        ev = getattr(api, "order_data_event", None)
        if ev: ev.set()



