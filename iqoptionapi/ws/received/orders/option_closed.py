"""
Handler para mensajes de cierre de opciones Binary/Turbo y confirmaciones "option".
Maneja: "option" y "option-closed".
"""
from iqoptionapi.core.logger import get_logger

logger = get_logger(__name__)


class OptionClosed:
    """Procesa el cierre de opciones Binary/Turbo y notifica a check_win*."""

    def __call__(self, api, message):
        """
        Recibe el mensaje WS parseado y dispara los event stores.
        """
        try:
            msg = message.get("msg", {})
            # 'id' en mensaje "option", 'option_id' en mensaje "option-closed"
            order_id = msg.get("id") or msg.get("option_id")
            
            if order_id is None:
                if "request_id" in message:
                    api.buy_multi_option[str(message["request_id"])] = msg
                return

            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                pass

            # 1. Almacenamiento
            api.socket_option_closed[order_id] = message
            
            if hasattr(api, "order_async"):
                api.order_async[order_id][message.get("name", "option")] = message

            if message.get("microserviceName") == "binary-options":
                api.order_binary[order_id] = msg

            # 2. Notificación reactiva (Sprint 7)
            if hasattr(api, "listinfodata"):
                win_val = msg.get("win", msg.get("profit_amount"))
                game_state = msg.get("status", msg.get("game_state"))
                if win_val is not None:
                    api.listinfodata.set(win_val, game_state, order_id)

            # SPRINT 14: WS Event Bridge — desbloquear _wait_result
            # Detectar si es un mensaje de finalización (win/loose/equal)
            is_result = (
                msg.get("status") in ("win", "loose", "equal") or 
                message.get("name") == "option-closed" or
                "win" in msg or 
                "profit_amount" in msg
            )

            if is_result:
                ev_store = getattr(self, 'result_event_store', None) or getattr(api, 'result_event_store', None)
                if ev_store is not None and order_id:
                    ev_store[order_id].set()
                
                # Digital fallback compatibility
                ev_sock = getattr(self, 'socket_option_closed_event', None) or getattr(api, 'socket_option_closed_event', None)
                if ev_sock is not None and order_id:
                    ev_sock[order_id].set()

            logger.debug("option_closed: order_id=%s result notified", order_id)

        except Exception as e:
            logger.warning("option_closed handler error: %s", e)

