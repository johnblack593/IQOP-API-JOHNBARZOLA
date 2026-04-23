"""Module for IQ option websocket."""

def socket_option_closed(api, message):
    if message["name"] == "socket-option-closed":
        id = message["msg"]["id"]
        api.socket_option_closed[id] = message
        # S1-T4: Notify per-order event store for non-blocking check_win_v3/v4()
        if hasattr(api, 'socket_option_closed_event'):
            ev = api.socket_option_closed_event[id]
            ev.set()
