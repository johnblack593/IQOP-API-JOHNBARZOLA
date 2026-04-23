"""
Module for portfolio.get-positions WS response handling.
Stores open positions keyed by instrument_type and fires an event
so callers can wait non-blockingly.
"""


class PortfolioPositions:
    """Handles portfolio.get-positions WS responses."""

    @staticmethod
    def handle(api, message):
        """
        Called by the message router when 'portfolio.get-positions' arrives.
        Populates api.open_positions[instrument_type] and fires
        api.open_positions_event.
        """
        msg = message.get("msg", {})
        positions_list = msg.get("positions", [])

        # Determine instrument_type from the first position or from request body
        instrument_type = None
        if positions_list:
            instrument_type = positions_list[0].get("instrument_type")
        if not instrument_type:
            # fallback: try to extract from the message body
            body = message.get("body", {})
            instrument_type = body.get("instrument_type", "unknown")

        api.open_positions[instrument_type] = positions_list

        ev = getattr(api, "open_positions_event", None)
        if ev:
            ev.set()
