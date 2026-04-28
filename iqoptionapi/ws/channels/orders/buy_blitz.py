"""
Channel for placing Blitz orders using the modern protocol.

Uses: binary-options.open-option (v2.0)
Reverse-engineered from Chrome 124 browser session (2026-04-28).
"""

from iqoptionapi.ws.channels.base import Base


class BuyBlitz(Base):
    """
    Places a Blitz order.
    
    Browser payload example:
        {
            "name": "binary-options.open-option",
            "version": "2.0",
            "body": {
                "user_balance_id": 987654321,
                "active_id": 1861,
                "option_type_id": 12,
                "direction": "call",
                "expired": 1777402754,
                "refund_value": 0,
                "price": 1,
                "value": 1171165,
                "profit_percent": 83,
                "expiration_size": 180
            }
        }
    """
    name = "sendMessage"

    def __call__(
        self,
        active_id,
        direction,
        amount,
        current_price,
        expiration_size=180, # Default Blitz duration in seconds
        profit_percent=83,    # Captured from browser
        request_id=None
    ):
        # value = price * 10^6 (assuming 6 decimals for EURUSD Blitz)
        # TODO: Dynamic precision detection if needed.
        multiplied_value = int(float(current_price) * 1000000)
        
        # Expiration is current time + expiration_size
        import time
        expired = int(time.time()) + int(expiration_size)

        body = {
            "user_balance_id": int(self.api.balance_id),
            "active_id": int(active_id),
            "option_type_id": 12, # Blitz
            "direction": str(direction).lower(),
            "expired": expired,
            "refund_value": 0,
            "price": float(amount),
            "value": multiplied_value,
            "profit_percent": int(profit_percent),
            "expiration_size": int(expiration_size)
        }

        data = {
            "name": "binary-options.open-option",
            "version": "2.0",
            "body": body,
        }
        self.send_websocket_request(self.name, data, request_id)
