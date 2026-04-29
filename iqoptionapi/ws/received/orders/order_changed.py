"""
Module for IQ Option websocket received order-changed message.
"""
from iqoptionapi.core.logger import get_logger

class OrderChanged:
    """
    Handler for: order-changed
    Fires when a pending order changes status (e.g., filled, canceled).
    """
    def __call__(self, api, message):
        if message.get("name") == "order-changed":
            body = message.get("msg", message.get("body", message))
            order_id = str(body.get("id"))
            status = body.get("status")
            
            if not hasattr(api, "order_changed_data"):
                api.order_changed_data = {}
            
            api.order_changed_data[order_id] = body
            
            # Signal events (Sprint 1 event store pattern)
            if hasattr(api, "order_data_event_store"):
                if order_id in api.order_data_event_store:
                    api.order_data_event_store[order_id].set()
            
            # Specific status signaling
            if status in ["filled", "active"]:
                get_logger(__name__).info("Order %s ACTIVATED (status: %s)", order_id, status)
                
            elif status == "canceled":
                get_logger(__name__).warning("Order %s CANCELED", order_id)
                # Signal cancel event if someone is waiting for it
                if hasattr(api, "order_canceled_event"):
                    # Check if it's a dict or single event
                    if isinstance(api.order_canceled_event, dict):
                        if order_id in api.order_canceled_event:
                            api.order_canceled_event[order_id].set()
                    else:
                        api.order_canceled_event.set()

