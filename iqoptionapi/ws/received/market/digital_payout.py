"""Module for IQ option websocket digital-payout handler."""

def digital_payout(api, message):
    if message["name"] == "digital-payout":
        # Structure: {"name":"digital-payout","msg":{"asset_id":76,"payout":87}}
        msg = message["msg"]
        api.digital_payout = msg.get("payout", 0)
        api.digital_payout_event.set()
