"""Module for IQ option websocket."""

def balances(api, message):
    if message["name"] == "balances":
        api.balances_raw = message
        if hasattr(api, 'balances_raw_event'):
            api.balances_raw_event.set()
