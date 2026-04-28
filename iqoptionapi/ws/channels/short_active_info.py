from iqoptionapi.ws.channels.base import Base

class SubscribeShortActiveInfo(Base):
    """
    Channel for: subscribeMessage -> short-active-info
    """
    name = "subscribeMessage"

    def __call__(self, active_id):
        data = {
            "name": "short-active-info",
            "msg": {
                "active_id": int(active_id)
            }
        }
        self.send_packet(data)
