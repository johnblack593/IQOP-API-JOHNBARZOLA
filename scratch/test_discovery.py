import os
import time
import logging
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

def test_discovery():
    load_dotenv()
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    
    iq = IQ_Option(email, password)
    status, reason = iq.connect()
    
    if not status:
        print(f"Connect failed: {reason}")
        return

    print("Connected. Waiting for asset discovery...")
    # Wait for initialization to complete
    time.sleep(10)
    
    data = iq.get_all_open_time()
    
    for type_name in ["binary", "turbo", "digital", "cfd", "forex", "crypto"]:
        assets = data.get(type_name, {})
        open_assets = [k for k, v in assets.items() if v.get("open")]
        print(f"{type_name.capitalize()} assets: {len(assets)} | Open: {len(open_assets)}")
        if open_assets:
            print(f"  First open {type_name}: {open_assets[0]}")

    iq.api.close()

if __name__ == "__main__":
    test_discovery()
