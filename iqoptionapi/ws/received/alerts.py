"""
Handler for price alerts.
"""
from iqoptionapi.logger import get_logger

logger = get_logger(__name__)

def alerts(api, message):
    """
    Fires when the server sends a price alert notification.
    """
    if message["name"] == "alerts":
        api.alerts_data = message.get("msg", {})
        if hasattr(api, "alerts_event"):
            api.alerts_event.set()
        logger.info("Price alert received: %s", api.alerts_data)
