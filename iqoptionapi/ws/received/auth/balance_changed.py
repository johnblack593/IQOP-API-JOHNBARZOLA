"""Module for IQ option websocket."""

def balance_changed(api, message):
    if message['name'] == 'balance-changed':
        balance = message.get('msg', {}).get('current_balance', {})
        if isinstance(balance, dict):
            if "amount" in balance:
                api.profile.balance = balance["amount"]
            if "id" in balance:
                api.profile.balance_id = balance["id"]
            if "type" in balance:
                api.profile.balance_type = balance["type"]
