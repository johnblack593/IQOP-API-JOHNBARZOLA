"""
Handler para mensajes socket-option-closed.
"""
from iqoptionapi.logger import get_logger

logger = get_logger(__name__)


class SocketOptionClosed:
    """Procesa el cierre de opciones y notifica a check_win_v3/v4."""

    def __call__(self, api, message):
        try:
            msg = message.get("msg", {})
            order_id = msg.get("id")
            
            if order_id is None:
                return

            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                pass

            api.socket_option_closed[order_id] = message
            
            if hasattr(api, "socket_option_closed_event"):
                api.socket_option_closed_event[order_id].set()
            
            if hasattr(api, "result_event_store"):
                api.result_event_store[order_id].set()

            logger.debug("socket_option_closed: order_id=%s notified", order_id)

        except Exception as e:
            logger.warning("socket_option_closed handler error: %s", e)
