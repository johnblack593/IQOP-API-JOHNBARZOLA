import iqoptionapi.constants as OP_code

def initialization_data(api, message):
    if message["name"] == "initialization-data":
        msg = message["msg"]
        from iqoptionapi.logger import get_logger
        get_logger(__name__).info("Received initialization-data keys: %s", list(msg.keys()))
        api.api_option_init_all_result_v2 = msg
        api._init_data_received = True
        ev = getattr(api, "api_option_init_all_result_v2_event", None)
        if ev: ev.set()

        # Dynamic population of ACTIVES constants from all instrument types
        # This ensures OTC and newly added assets are always resolvable
        for instrument_type in ["binary", "turbo", "digital", "blitz", "cfd", "forex", "crypto"]:
            type_data = msg.get(instrument_type, {})
            actives = type_data.get("actives", {})
            for active_id, active_data in actives.items():
                raw_name = str(active_data.get("name", ""))
                if "." in raw_name:
                    name = raw_name.split(".")[1]
                else:
                    name = raw_name
                
                if name:
                    OP_code.ACTIVES[name] = int(active_id)

        # Extract Blitz instrument catalog (not available via get_instruments)
        blitz_raw = msg.get("blitz", {})
        blitz_actives = blitz_raw.get("actives", {})
        parsed = {}
        for active_id, active_data in blitz_actives.items():
            raw_name = str(active_data.get("name", ""))
            if "." in raw_name:
                name = raw_name.split(".")[1]
            else:
                name = raw_name
            
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
