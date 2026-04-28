"""Module for IQ option websocket."""

def underlying_list(api, message):
    if message["name"] == "underlying-list":
        api.underlying_list_data = message["msg"]
        
        # Backward compatibility for get_instruments mapping
        # `underlying-list` returns {"items": [...]}, which we map to {"instruments": [...]}
        # so that `stable_api.py` fallback works natively.
        items = message.get("msg", {}).get("items", [])
        if items:
            api.instruments = {"instruments": items}
            if hasattr(api, 'instruments_event'):
                api.instruments_event.set()

        ev = getattr(api, "underlying_list_data_event", None)
        if ev: ev.set()
