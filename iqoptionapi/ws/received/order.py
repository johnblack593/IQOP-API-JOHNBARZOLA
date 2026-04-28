def order(api, message):
    if message["name"] in ["order", "orders-state"]:
        api.order_data = message
        ev = getattr(api, "order_data_event", None)
        if ev: ev.set()
