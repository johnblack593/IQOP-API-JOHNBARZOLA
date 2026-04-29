"""
Handler para mensajes socket-option-closed.
"""
from iqoptionapi.core.logger import get_logger

logger = get_logger(__name__)


class SocketOptionClosed:
    """Procesa el cierre de opciones y notifica a check_win_v3/v4."""

    def __call__(self, api, message):
        try:
            msg = message.get("msg", {})
            order_id = msg.get("id")
            logger.info("RECEIVED socket_option_closed order_id=%r", order_id)
            
            if order_id is None:
                return

            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                pass

            api.socket_option_closed[order_id] = message
            
            # SPRINT 14: WS Event Bridge — desbloquear _wait_result
            ev_sock = getattr(self, 'socket_option_closed_event', None) or getattr(api, 'socket_option_closed_event', None)
            if ev_sock is not None and order_id:
                ev_sock[order_id].set()
            
            ev_res = getattr(self, 'result_event_store', None) or getattr(api, 'result_event_store', None)
            if ev_res is not None and order_id:
                ev_res[order_id].set()

            logger.debug("socket_option_closed: order_id=%s notified", order_id)

        except Exception as e:
            logger.warning("socket_option_closed handler error: %s", e)

