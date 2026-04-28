"""Module for IQ option websocket."""

def list_info_data(api, message):
    if message["name"] == "listInfoData":
        for get_m in message["msg"]:
            api.listinfodata.set(get_m["win"], get_m["game_state"], get_m["id"])
            # S1-T4: Notify per-order event store for non-blocking check_win()
            order_id = get_m.get("id")
            if order_id and hasattr(api, 'result_event_store'):
                api.result_event_store[order_id].set()
