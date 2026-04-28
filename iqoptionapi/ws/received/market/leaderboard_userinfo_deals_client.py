"""Module for IQ option websocket."""

def leaderboard_userinfo_deals_client(api, message):
    if message["name"] == "leaderboard-userinfo-deals-client":
        api.leaderboard_userinfo_deals_client = message["msg"]
        ev = getattr(api, "leaderboard_userinfo_deals_client_event", None)
        if ev: ev.set()
