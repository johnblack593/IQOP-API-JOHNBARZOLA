"""Module for IQ option websocket."""

def leaderboard_deals_client(api, message):
    if message["name"] == "leaderboard-deals-client":
        api.leaderboard_deals_client = message["msg"]
        if hasattr(api, 'leaderboard_deals_client_event'):
            api.leaderboard_deals_client_event.set()