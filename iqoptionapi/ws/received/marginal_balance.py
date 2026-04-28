"""
Module for IQ Option websocket received marginal-balance message.
"""

class MarginalBalance:
    """
    Handler for: marginal-balance
    Fires when the available margin balance changes.
    """
    def __call__(self, api, message):
        if message.get("name") == "marginal-balance":
            body = message.get("msg", message.get("body", {}))
            
            # Structure: { "instrument_type": "forex", "balance": 123.45 }
            instrument_type = body.get("instrument_type")
            balance = body.get("balance")
            
            if not hasattr(api, "marginal_balance"):
                api.marginal_balance = {}
                
            if instrument_type:
                api.marginal_balance[instrument_type] = balance
            
            # Signal balance event
            ev = getattr(api, "marginal_balance_event", None)
            if ev: ev.set()
