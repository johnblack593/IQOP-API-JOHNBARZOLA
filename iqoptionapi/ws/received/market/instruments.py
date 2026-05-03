from iqoptionapi.core.logger import get_logger

def instruments(api, message):
    name = message.get("name")
    msg = message.get("msg")
    
    if name in ("instruments", "instruments-list"):
        api.instruments = msg
        itype = msg.get("type", "unknown") or msg.get("instrument_type", "unknown")
        count = len(msg.get("instruments", []))
        get_logger(__name__).info("WS instruments received: name=%s, type=%s, count=%d", name, itype, count)
        
        # SPRINT 2: Store dynamic leverage profiles
        if "dynamic_leverage_profiles" in msg:
            if not hasattr(api, "dynamic_leverage_profiles"):
                api.dynamic_leverage_profiles = {}
            for profile in msg["dynamic_leverage_profiles"]:
                api.dynamic_leverage_profiles[profile["id"]] = profile
        
        if hasattr(api, 'instruments_event'):
            api.instruments_event.set()

    elif name == "instruments-list-changed":
        # Sprint 4: Real-time asset status updates
        itype = msg.get("type")
        get_logger(__name__).info("WS instruments-list-changed: type=%s", itype)
        
        from iqoptionapi.core import constants
        
        for ins in msg.get("instruments", []):
            active_name = ins.get("name")
            active_id = ins.get("id")
            is_open = not ins.get("is_suspended", False)
            
            # 1. Update ACTIVES dynamically if new
            if active_name and active_id:
                constants.ACTIVES[active_name] = active_id
                
            # 2. Trigger status changed callback if available
            callback = getattr(api, "on_instrument_status_changed", None)
            if callback:
                try:
                    callback(itype, active_name, is_open, ins)
                except Exception as e:
                    get_logger(__name__).error("on_instrument_status_changed callback fail: %s", e)
        
        # Signal change event
        ev = getattr(api, "instruments_changed_event", None)
        if ev: ev.set()

