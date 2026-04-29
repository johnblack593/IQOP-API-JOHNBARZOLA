"""
Handler for price alerts.
"""
from iqoptionapi.core.logger import get_logger

logger = get_logger(__name__)

class Alerts:
    """
    Handler for price alerts.
    Handles both confirmation of creation and triggered alerts.
    """
    def __init__(self):
        pass

    def __call__(self, api, message):
        """
        Fires when the server sends a price alert notification.
        """
        if message["name"] == "alerts":
            msg = message.get("msg", {})
            api.alerts_data = msg
            
            # SPRINT 8: Detect if this is a confirmation or a triggered alert
            status = msg.get("status")
            alert_id = msg.get("id")
            
            if status == "created":
                logger.info("Price alert CREATED successfully: ID=%s", alert_id)
            else:
                logger.info("Price alert TRIGGERED: %s", msg)
                
            if hasattr(api, "alerts_event"):
                api.alerts_event.set()

