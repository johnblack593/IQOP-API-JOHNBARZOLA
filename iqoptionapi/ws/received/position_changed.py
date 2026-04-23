"""
Handler para mensajes position-changed.
Maneja cierre de posiciones Digital/CFD/Forex.
"""
from iqoptionapi.logger import get_logger

logger = get_logger(__name__)


class PositionChanged:
    """Procesa cambios en posiciones y notifica a check_win_digital*."""

    def __call__(self, api, message):
        try:
            msg = message.get("msg", {})
            order_id = None
            
            microservice = message.get("microserviceName")
            source = msg.get("source")
            
            if microservice == "portfolio" and (source in ("digital-options", "trading")):
                if msg.get("raw_event") and msg["raw_event"].get("order_ids"):
                    order_id = msg["raw_event"]["order_ids"][0]
            elif microservice == "portfolio" and source == "binary-options":
                order_id = msg.get("external_id")
            else:
                order_id = msg.get("position_id") or msg.get("id")

            if order_id is None:
                api.position_changed = message
                return

            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                pass

            if hasattr(api, "order_async"):
                api.order_async[order_id][message.get("name")] = message

            status = msg.get("status")
            logger.debug("position_changed raw status=%r source=%r order_id=%s", status, source, order_id)
            
            if status in ("closed", "expired", "canceled", "sold"):
                ev_global = getattr(api, "position_changed_event", None)
                if ev_global:
                    ev_global.set()

                if hasattr(api, "position_changed_event_store"):
                    api.position_changed_event_store[order_id].set()
                
                if hasattr(api, "result_event_store"):
                    api.result_event_store[order_id].set()
                    
                logger.debug("position_changed: order_id=%s status=%s signaled", order_id, status)

        except Exception as e:
            logger.warning("position_changed handler error: %s", e)
