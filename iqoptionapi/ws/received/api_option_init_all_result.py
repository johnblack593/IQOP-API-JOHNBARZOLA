"""Module for IQ option websocket."""

def api_option_init_all_result(api, message):
    if message["name"] == "api_option_init_all_result":
        api.api_option_init_all_result = message["msg"]
        api._init_data_received = True
        ev = getattr(api, "api_option_init_all_result_event", None)
        if ev: ev.set()
