"""Module for IQ option websocket."""

def profile(api, message):
    if message["name"] == "profile":
        api.profile.msg = message["msg"]
        if hasattr(api, 'profile_msg_event'):
            api.profile_msg_event.set()
        if api.profile.msg != False:
            msg = message.get("msg", {})
            # Safe balance extraction
            if "balance" in msg:
                api.profile.balance = msg["balance"]
            # Set Default account
            if api.balance_id == None:
                for balance in msg.get("balances", []):
                    if balance.get("type") == 4:
                        api.balance_id = balance["id"]
                        if hasattr(api, 'balance_id_event'):
                            api.balance_id_event.set()
                        break
            if "balance_id" in msg:
                api.profile.balance_id = msg["balance_id"]
            if "balance_type" in msg:
                api.profile.balance_type = msg["balance_type"]
            if "balances" in msg:
                api.profile.balances = msg["balances"]
