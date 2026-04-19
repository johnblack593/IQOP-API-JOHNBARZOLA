"""Module for IQ option websocket."""

def training_balance_reset(api, message):
    if message["name"] == "training-balance-reset":
        is_success = message["msg"].get("isSuccessful", False)
        # Some API versions return {"message": "Balance was successfully reset"} instead
        if not is_success and "successfully" in message["msg"].get("message", ""):
            is_success = True
        api.training_balance_reset_request = is_success
        if hasattr(api, 'training_balance_reset_request_event'):
            api.training_balance_reset_request_event.set()