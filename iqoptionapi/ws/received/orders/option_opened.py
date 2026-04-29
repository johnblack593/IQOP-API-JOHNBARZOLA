"""Module for IQ option websocket."""
from iqoptionapi.core.logger import get_logger

def option_opened(api, message):
    if message["name"] == "option-opened":
        option_id = message["msg"]["option_id"]
        api.order_async[int(option_id)][message["name"]] = message
        
        # Correlación con el request_id pendiente (Sprint 3)
        if api.pending_buy_ids:
            req_id = api.pending_buy_ids.popleft()
            if req_id not in api.buy_multi_option:
                api.buy_multi_option[req_id] = {}
            api.buy_multi_option[req_id]["id"] = option_id
            get_logger(__name__).debug("Correlated req_id=%s with option_id=%s", req_id, option_id)
            # También disparamos el evento para que buy() despierte si aún no lo hizo
            ev = getattr(api, "result_event", None)
            if ev: ev.set()
        else:
            get_logger(__name__).debug("No pending req_id for option_id=%s", option_id)

