"""Module for IQ option websocket."""

def buy_complete(api, message):
    if message['name'] == 'buyComplete':
        msg = message.get("msg", {})
        api.buy_successful = msg.get("isSuccessful")
        result = msg.get("result", {})
        api.buy_id = result.get("id") if isinstance(result, dict) else None
        ev = getattr(api, "buy_complete_event", None)
        if ev: ev.set()
