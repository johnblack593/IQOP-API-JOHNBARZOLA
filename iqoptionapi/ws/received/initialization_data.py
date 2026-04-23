"""Module for IQ option websocket initialization-data handler."""

def initialization_data(api, message):
    if message["name"] == "initialization-data":
        api.api_option_init_all_result_v2 = message["msg"]
        api._init_data_received = True
        ev = getattr(api, "api_option_init_all_result_v2_event", None)
        if ev: ev.set()

        # Extract Blitz instrument catalog (not available via get_instruments)
        blitz_raw = message["msg"].get("blitz", {})
        blitz_actives = blitz_raw.get("actives", {})
        parsed = {}
        for active_id, active_data in blitz_actives.items():
            name = str(active_data.get("name", ""))
            if "." in name:
                name = name.split(".")[1]
            ticker = active_data.get("ticker", name)
            enabled = active_data.get("enabled", False)
            is_suspended = active_data.get("is_suspended", True)
            expirations = active_data.get("option", {}).get("expiration_times", [])
            parsed[name] = {
                "id": int(active_id),
                "ticker": ticker,
                "enabled": enabled,
                "is_suspended": is_suspended,
                "open": enabled and not is_suspended,
                "expirations": expirations,
            }
        api.blitz_instruments = parsed
