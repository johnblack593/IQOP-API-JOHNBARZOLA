"""Module for IQ option websocket."""

class OvernightFee:
    """
    Handler for: overnight-fee
    Almacena comisiones por mantener posiciones abiertas (swap).
    """
    def __init__(self):
        pass

    def __call__(self, api, message):
        if message["name"] == "overnight-fee":
            msg = message.get("msg", {})
            position_id = msg.get("position_id")
            if position_id:
                if not hasattr(api, "overnight_fee_data"):
                    api.overnight_fee_data = {}
                api.overnight_fee_data[position_id] = msg
            
            # Legacy fallback
            api.overnight_fee = message
            
            ev = getattr(api, "overnight_fee_event", None)
            if ev: ev.set()

