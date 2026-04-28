"""
Channel for subscribing to instrument list changes.

Uses: subscribeMessage for marginal-*.instruments-list-changed
Reverse-engineered from Chrome 124 browser session (2026-04-28).
"""

from iqoptionapi.ws.channels.base import Base


class SubscribeInstrumentsList(Base):
    """
    Subscribes to instrument list changes.
    """
    name = "subscribeMessage"

    def __call__(self, instrument_type):
        """
        :param instrument_type: "forex", "cfd", "crypto"
        """
        api_type = str(instrument_type).lower()
        if api_type == "forex":
            msg_name = "marginal-forex-instruments.instruments-list-changed"
        elif api_type == "cfd":
            msg_name = "marginal-cfd-instruments.instruments-list-changed"
        elif api_type == "crypto":
            msg_name = "marginal-crypto-instruments.instruments-list-changed"
        else:
            raise ValueError(f"Unknown instrument_type '{instrument_type}' for instruments-list subscription")

        data = {
            "name": msg_name,
            "version": "1.0",
        }
        self.send_websocket_request(self.name, data)


class UnsubscribeInstrumentsList(Base):
    """
    Unsubscribes from instrument list changes.
    """
    name = "unsubscribeMessage"

    def __call__(self, instrument_type):
        api_type = str(instrument_type).lower()
        if api_type == "forex":
            msg_name = "marginal-forex-instruments.instruments-list-changed"
        elif api_type == "cfd":
            msg_name = "marginal-cfd-instruments.instruments-list-changed"
        elif api_type == "crypto":
            msg_name = "marginal-crypto-instruments.instruments-list-changed"
        else:
            raise ValueError(f"Unknown instrument_type '{instrument_type}' for instruments-list unsubscription")

        data = {
            "name": msg_name,
            "version": "1.0",
        }
        self.send_websocket_request(self.name, data)
