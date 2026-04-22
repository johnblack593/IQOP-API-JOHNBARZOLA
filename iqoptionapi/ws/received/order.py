"""Module for IQ option websocket."""

def order(api, message):
    if message["name"] == "order":
        api.order_data = message
        ev = getattr(api, "order_data_event", None)
        if ev: ev.set()
