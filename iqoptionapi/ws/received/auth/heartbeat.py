"""Module for IQ option websocket."""
from iqoptionapi.core.logger import get_logger

def heartbeat(api, message):
    if message["name"] == "heartbeat":
        get_logger(__name__).debug("Heartbeat received: %s", message["msg"])
        api.heartbeat(message["msg"])
        
        cb = getattr(api, '_heartbeat_callback', None)
        if cb is not None and callable(cb):
            cb()
        else:
            get_logger(__name__).debug("No heartbeat callback found on api")
