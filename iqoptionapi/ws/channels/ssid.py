"""Module for IQ option API ssid websocket chanel."""

from iqoptionapi.ws.channels.base import Base


class Ssid(Base):
    """Class for IQ option API ssid websocket chanel."""
    # pylint: disable=too-few-public-methods

    name = "authenticate"

    def __call__(self, ssid):
        """Method to send message to authenticate websocket chanel.

        :param ssid: The session identifier.
        """
        import time
        request_id = int(str(time.time()).split('.')[1])
        payload = {
            "name": "authenticate",
            "msg": {
                "ssid": ssid,
                "protocol": 3,
                "session_id": "".join(__import__('random').choices(__import__('string').ascii_lowercase + __import__('string').digits, k=16)),
                "client_session_id": "".join(__import__('random').choices(__import__('string').ascii_lowercase + __import__('string').digits, k=16))
            },
            "request_id": str(request_id)
        }
        import json
        self.api.websocket_client.wss.send(json.dumps(payload))
