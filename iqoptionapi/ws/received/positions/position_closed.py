"""
Module for IQ Option websocket received position-closed message.
"""
from iqoptionapi.core.logger import get_logger

class PositionClosed:
    """
    Handler for: position-closed
    Fires when a position is definitively closed (PnL settled).
    """
    def __call__(self, api, message):
        if message.get("name") == "position-closed":
            body = message.get("msg", message.get("body", message))
            
            # Identifiers
            order_id = body.get("order_id")
            external_id = body.get("external_id")
            
            # Storage
            if not hasattr(api, "position_closed_result"):
                api.position_closed_result = {}
            
            key = str(external_id or order_id)
            api.position_closed_result[key] = body
            
            # Signal events (reutiliza event store de SPRINT 7)
            if hasattr(api, "position_changed_event_store"):
                if key in api.position_changed_event_store:
                    api.position_changed_event_store[key].set()
            
            # Legacy event for compatibility
            api.close_position_data = body
            if hasattr(api, "position_closed_event"):
                api.position_closed_event.set()

            # Extraer PnL final
            pnl = body.get("pnl") or body.get("close_profit") or 0.0
            result = "win" if pnl > 0 else ("loss" if pnl < 0 else "draw")
            
            # Journaling (si está habilitado en stable_api)
            if hasattr(api, "trade_journal") and api.trade_journal:
                try:
                    api.trade_journal.record(
                        order_id=key,
                        result=result,
                        active_id=body.get("active_id"),
                        amount=body.get("invest"),
                        profit=float(pnl)
                    )
                except Exception as e:
                    get_logger(__name__).error("position_closed: journal record fail: %s", e)

