from iqoptionapi.logger import get_logger

def instruments(api, message):
    if message["name"] in ("instruments", "instruments-list"):
            api.instruments = message["msg"]
            msg = message["msg"]
            itype = msg.get("type", "unknown") or msg.get("instrument_type", "unknown")
            count = len(msg.get("instruments", []))
            get_logger(__name__).info("WS instruments received: name=%s, type=%s, count=%d", message["name"], itype, count)
            
            # SPRINT 2: Store dynamic leverage profiles for min_leverage detection
            if "dynamic_leverage_profiles" in msg:
                if not hasattr(api, "dynamic_leverage_profiles"):
                    api.dynamic_leverage_profiles = {}
                for profile in msg["dynamic_leverage_profiles"]:
                    api.dynamic_leverage_profiles[profile["id"]] = profile
            
            if hasattr(api, 'instruments_event'):
                api.instruments_event.set()

