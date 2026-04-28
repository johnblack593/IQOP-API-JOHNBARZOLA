"""Module for IQ option websocket."""

def deferred_orders(api, message):
    if message["name"] == "deferred-orders":
        api.deferred_orders = message
        ev = getattr(api, "deferred_orders_event", None)
        if ev: ev.set()
