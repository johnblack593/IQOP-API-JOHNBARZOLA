"""Module for IQ option websocket."""

def heartbeat(api, message):
    if message["name"] == "heartbeat":
        api.heartbeat(message["msg"])
