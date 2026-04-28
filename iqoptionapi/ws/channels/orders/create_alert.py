"""
Channel for creating price alerts.
Uses: create-alert (v1.0)
"""

from iqoptionapi.ws.channels.base import Base

class CreateAlert(Base):
    """
    Creates a price alert for a specific active.
    """
    name = "sendMessage"

    def __call__(self, active_id, price, direction, request_id=None):
        """
        :param active_id: The ID of the active asset.
        :param price: The target price for the alert.
        :param direction: "above" or "below".
        """
        data = {
            "name": "create-alert",
            "version": "1.0",
            "body": {
                "active_id": int(active_id),
                "price": float(price),
                "type": str(direction).lower()
            }
        }
        self.send_websocket_request(self.name, data, request_id)
