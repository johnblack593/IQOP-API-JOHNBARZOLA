"""Module for IQ option websocket."""

def overnight_fee(api, message):
    if message["name"] == "overnight-fee":
        api.overnight_fee = message
        ev = getattr(api, "overnight_fee_event", None)
        if ev: ev.set()
