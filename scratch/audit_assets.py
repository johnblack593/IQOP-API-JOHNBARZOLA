import os
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv
import json

load_dotenv()

def audit_all_assets():
    api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
    SSID = "05ac28045097edb0fcde0d87e0ce207q"
    status, reason = api.connect(ssid=SSID)
    
    if not status:
        print(f"Connection failed: {reason}")
        return

    init_data = api.get_all_init_v2()
    
    results = {}
    for itype in ["binary", "turbo", "digital", "blitz", "cfd", "forex", "crypto"]:
        actives = init_data.get(itype, {}).get("actives", {})
        results[itype] = len(actives)
        if "EURUSD" in str(actives) or "EURUSD-OTC" in str(actives):
            print(f"Found EURUSD/OTC in {itype}")

    print(json.dumps(results, indent=2))
    
    api.close()

if __name__ == "__main__":
    audit_all_assets()
