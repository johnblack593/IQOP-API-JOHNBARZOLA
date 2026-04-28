"""
Module for IQ Option websocket received order and orders-state messages.
"""

class OrderState:
    """
    Handler for: order and orders-state
    Fires when a single order status is received or during bulk synchronization.
    """
    def __call__(self, api, message):
        name = message.get("name")
        
        if name == "order":
            api.order_data = message
            ev = getattr(api, "order_data_event", None)
            if ev: ev.set()
            
        elif name == "orders-state":
            # Bulk sync: [ {id, status, ...}, ... ]
            body = message.get("msg", message.get("body", []))
            if not hasattr(api, "orders_state_data"):
                api.orders_state_data = {}
                
            # Refresh the entire pending orders state
            api.orders_state_data = {str(o["id"]): o for o in body}
            
            # Signal bulk sync event
            ev = getattr(api, "orders_state_event", None)
            if ev: ev.set()
