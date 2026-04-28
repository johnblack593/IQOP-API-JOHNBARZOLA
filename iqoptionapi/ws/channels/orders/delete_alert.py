"""
Channel for deleting price alerts.
Uses: delete-alert (v1.0)
"""

from iqoptionapi.ws.channels.base import Base

class DeleteAlert(Base):
    """
    Deletes a price alert by ID.
    """
    name = "sendMessage"

    def __call__(self, alert_id, request_id=None):
        """
        :param alert_id: The ID of the alert to delete.
        """
        data = {
            "name": "delete-alert",
            "version": "1.0",
            "body": {
                "id": int(alert_id)
            }
        }
        self.send_websocket_request(self.name, data, request_id)
