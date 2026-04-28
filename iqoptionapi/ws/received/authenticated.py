"""Module for IQ option websocket received authenticated message."""

def authenticated(api, message):
    if message.get("name") == "authenticated":
        if hasattr(api, "authenticated_event"):
            api.authenticated_event.set()
