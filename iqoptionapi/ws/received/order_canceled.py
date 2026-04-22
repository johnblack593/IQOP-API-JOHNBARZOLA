"""Module for IQ option websocket."""

def order_canceled(api, message):
    if message["name"] == "order-canceled":
        api.order_canceled = message
        ev = getattr(api, "order_canceled_event", None)
        if ev: ev.set()
