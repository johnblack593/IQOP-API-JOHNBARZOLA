import time

class ShortActiveInfo:
    """
    Handler for: short-active-info
    Datos rápidos de activo: precio actual, spread, estado (open/closed).
    """
    def __init__(self):
        pass
    
    def __call__(self, api, message):
        msg = message.get("msg", {})
        active_id = msg.get("active_id") or msg.get("id")
        if active_id:
            if not hasattr(api, "short_active_info_data"):
                api.short_active_info_data = {}
            
            api.short_active_info_data[active_id] = {
                "ask": msg.get("ask"),
                "bid": msg.get("bid"),
                "spread": msg.get("spread"),
                "is_open": msg.get("is_active", True),
                "updated_at": time.time(),
                "raw": msg
            }
            
            if hasattr(api, "short_active_info_event"):
                api.short_active_info_event.set()
