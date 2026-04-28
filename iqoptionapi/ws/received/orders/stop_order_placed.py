"""
Module for IQ Option websocket received stop-order-placed message.
"""

class StopOrderPlaced:
    """
    Handler for: stop-order-placed
    Fires when the server confirms a pending/stop order was accepted.
    Populates api.stop_order_placed_result and sets api.stop_order_placed_event.
    """
    def __call__(self, api, message):
        if message.get("name") == "stop-order-placed":
            # Body usually contains the data
            body = message.get("msg", message.get("body", {}))
            order_id = body.get("id") or body.get("order_id")
            
            api.stop_order_placed_result = body
            
            # Correlated event handling (Sprint 1 pattern)
            if hasattr(api, "stop_order_placed_event"):
                if isinstance(api.stop_order_placed_event, dict):
                    if order_id is not None:
                        oid_str = str(order_id)
                        if oid_str in api.stop_order_placed_event:
                            api.stop_order_placed_event[oid_str].set()
                elif hasattr(api.stop_order_placed_event, "set"):
                    api.stop_order_placed_event.set()
