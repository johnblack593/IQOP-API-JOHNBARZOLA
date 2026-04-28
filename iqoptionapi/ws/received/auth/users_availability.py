"""Module for IQ option websocket."""

def users_availability(api, message):
    if message["name"] == "users-availability":
        api.users_availability = message["msg"]
        ev = getattr(api, "users_availability_event", None)
        if ev: ev.set()
