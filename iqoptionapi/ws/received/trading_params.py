import time

class TradingParams:
    """
    Handler for: trading-params
    Dynamic trading parameters (payout, min/max amount).
    """
    def __init__(self):
        pass

    def __call__(self, api, message):
        msg = message.get("msg", {})
        active_id = msg.get("active_id")
        
        if active_id:
            if not hasattr(api, "trading_params_data"):
                api.trading_params_data = {}
            
            api.trading_params_data[active_id] = {
                "payout": msg.get("payout"),
                "min_amount": msg.get("min_amount"),
                "max_amount": msg.get("max_amount"),
                "updated_at": time.time(),
                "raw": msg
            }
            
            if hasattr(api, "trading_params_event"):
                api.trading_params_event.set()
