from iqoptionapi.logger import get_logger

def instruments(api, message):
    if message["name"] == "instruments":
            api.instruments = message["msg"]
            msg = message["msg"]
            itype = msg.get("type", "unknown")
            count = len(msg.get("instruments", []))
            get_logger(__name__).info("WS instruments received: type=%s, count=%d", itype, count)
            
            if hasattr(api, 'instruments_event'):
                api.instruments_event.set()

