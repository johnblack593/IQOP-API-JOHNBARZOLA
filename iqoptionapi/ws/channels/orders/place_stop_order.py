"""
Channel for placing Pending (Stop) orders using the modern protocol.

Uses: {prefix}.place-stop-order (v1.0)
Reverse-engineered from Chrome 124 browser session (2026-04-28).
"""

from iqoptionapi.ws.channels.base import Base

_INSTRUMENT_MAP = {
    "forex":  {"msg_prefix": "marginal-forex",  "id_prefix": "mf"},
    "cfd":    {"msg_prefix": "marginal-cfd",    "id_prefix": "mc"},
    "crypto": {"msg_prefix": "marginal-crypto", "id_prefix": "mcy"},
}

class PlaceStopOrder(Base):
    """
    Places a Pending (Stop) order.
    """
    name = "sendMessage"

    def __call__(
        self,
        instrument_type,
        active_id,
        side,
        margin,
        leverage,
        stop_price,
        take_profit=None,
        stop_loss=None,
        keep_position_open=True,
        request_id=None
    ):
        info = _INSTRUMENT_MAP.get(str(instrument_type).lower())
        if not info:
            raise ValueError(f"Unknown instrument_type '{instrument_type}' for stop order")

        msg_name = f"{info['msg_prefix']}.place-stop-order"
        instrument_id = f"{info['id_prefix']}.{active_id}"

        body = {
            "side": str(side).lower(),
            "user_balance_id": int(self.api.balance_id),
            "instrument_id": instrument_id,
            "instrument_active_id": int(active_id),
            "leverage": str(int(leverage)),
            "margin": str(margin),
            "is_margin_isolated": True,
            "stop_price": str(stop_price),
            "keep_position_open": bool(keep_position_open),
        }

        if take_profit:
            body["take_profit"] = {
                "type": str(take_profit.get("type", "pnl")),
                "value": str(take_profit.get("value"))
            }
        
        if stop_loss:
            body["stop_loss"] = {
                "type": str(stop_loss.get("type", "pnl")),
                "value": str(stop_loss.get("value"))
            }

        data = {
            "name": msg_name,
            "version": "1.0",
            "body": body,
        }
        self.send_websocket_request(self.name, data, request_id)
