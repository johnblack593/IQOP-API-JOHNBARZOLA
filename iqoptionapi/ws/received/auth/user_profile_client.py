"""Module for IQ option websocket."""

def user_profile_client(api, message):
    if message["name"] == "user-profile-client":
        api.user_profile_client = message["msg"]
        ev = getattr(api, "user_profile_client_event", None)
        if ev: ev.set()
