import os, json, time
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv
load_dotenv()

iq = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
iq.connect()

types = ["digital", "digital-option", "digital-option-v2", "dx-option"]
for t in types:
    print(f"Trying get-instruments with type: {t}")
    iq.api.instruments = None
    iq.api.send_websocket_request(name="get-instruments", msg={"type": t})
    time.sleep(3)
    insts = getattr(iq.api, "instruments", {})
    if insts and isinstance(insts, dict):
        count = len(insts.get("instruments", []))
        print(f"  Result count: {count}")
        if count > 0:
            print(f"  Sample: {insts.get('instruments')[0]['name']}")
    else:
        print(f"  No response for {t}")

iq.api.close()
