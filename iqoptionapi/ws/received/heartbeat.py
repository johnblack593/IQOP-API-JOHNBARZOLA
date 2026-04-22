"""Module for IQ option websocket."""

def heartbeat(api, message):
    if message["name"] == "heartbeat":
        api.heartbeat(message["msg"])
        
        cb = getattr(api, '_heartbeat_callback', None)
        if cb is not None and callable(cb):
            cb()
