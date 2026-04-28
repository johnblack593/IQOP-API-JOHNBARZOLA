import time

class ExchangeRate:
    """
    Handler for: exchange-rate-generated
    Conversion rates in real-time.
    """
    def __init__(self):
        pass

    def __call__(self, api, message):
        msg = message.get("msg", {})
        pair = f"{msg.get('from_currency')}/{msg.get('to_currency')}"
        
        if not hasattr(api, "exchange_rates"):
            api.exchange_rates = {}
        
        api.exchange_rates[pair] = {
            "rate": msg.get("rate"),
            "updated_at": time.time(),
            "raw": msg
        }
        
        if hasattr(api, "exchange_rate_event"):
            api.exchange_rate_event.set()
