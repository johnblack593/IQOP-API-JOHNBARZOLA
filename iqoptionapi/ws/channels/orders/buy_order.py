"""
Channel for placing margin market orders using the modern browser protocol.

Uses: marginal-{type}.place-market-order (v1.0)
NOT the legacy place-order-temp (v4.0).

Reverse-engineered from Chrome 124 browser session (2026-04-28).
"""

from iqoptionapi.ws.channels.base import Base


# Mapping from user-friendly instrument_type to server message prefix and instrument_id prefix
_INSTRUMENT_MAP = {
    "forex":  {"msg_prefix": "marginal-forex",  "id_prefix": "mf"},
    "cfd":    {"msg_prefix": "marginal-cfd",    "id_prefix": "mc"},
    "crypto": {"msg_prefix": "marginal-crypto", "id_prefix": "mcy"},
    # Also accept full names
    "marginal-forex":  {"msg_prefix": "marginal-forex",  "id_prefix": "mf"},
    "marginal-cfd":    {"msg_prefix": "marginal-cfd",    "id_prefix": "mc"},
    "marginal-crypto": {"msg_prefix": "marginal-crypto", "id_prefix": "mcy"},
}


class PlaceMarginOrder(Base):
    """
    Places a margin market order using the modern protocol.

    Browser payload example:
        {
            "name": "marginal-forex.place-market-order",
            "version": "1.0",
            "body": {
                "side": "buy",
                "user_balance_id": 987654321,
                "instrument_id": "mf.1",
                "instrument_active_id": 1,
                "leverage": "1000",
                "margin": "10",
                "is_margin_isolated": true,
                "take_profit": {"type": "pnl", "value": "5"},
                "stop_loss": {"type": "pnl", "value": "-3"},
                "keep_position_open": false
            }
        }
    """
    name = "sendMessage"

    def __call__(
        self,
        instrument_type,    # "forex", "cfd", "crypto"
        active_id,          # Numeric active ID (e.g., 1 for EURUSD)
        side,               # "buy" or "sell"
        margin,             # Amount in USD (e.g., 10)
        leverage,           # Leverage multiplier (e.g., 1000)
        take_profit=None,   # {"type": "pnl"|"price"|"percent", "value": <number>} or None
        stop_loss=None,     # {"type": "pnl"|"price"|"percent", "value": <number>} or None
        keep_position_open=False,
    ):
        instrument_type_lower = str(instrument_type).lower()
        if instrument_type_lower not in _INSTRUMENT_MAP:
            raise ValueError(
                f"Unknown instrument_type '{instrument_type}'. "
                f"Valid: {list(_INSTRUMENT_MAP.keys())}"
            )

        info = _INSTRUMENT_MAP[instrument_type_lower]
        msg_name = f"{info['msg_prefix']}.place-market-order"
        instrument_id = f"{info['id_prefix']}.{active_id}"

        body = {
            "side": str(side),
            "user_balance_id": int(self.api.balance_id),
            "instrument_id": instrument_id,
            "instrument_active_id": int(active_id),
            "leverage": str(int(leverage)),
            "margin": str(margin),
            "is_margin_isolated": True,
            "keep_position_open": bool(keep_position_open),
        }

        # TP/SL — sent as nested dicts with string values
        if take_profit is not None:
            body["take_profit"] = {
                "type": str(take_profit.get("type", "pnl")),
                "value": str(take_profit.get("value", 0)),
            }

        if stop_loss is not None:
            sl_value = stop_loss.get("value", 0)
            # Ensure negative for pnl type
            sl_type = str(stop_loss.get("type", "pnl"))
            if sl_type == "pnl" and float(sl_value) > 0:
                sl_value = -abs(float(sl_value))
            body["stop_loss"] = {
                "type": sl_type,
                "value": str(sl_value),
            }

        data = {
            "name": msg_name,
            "version": "1.0",
            "body": body,
        }
        self.send_websocket_request(self.name, data)
