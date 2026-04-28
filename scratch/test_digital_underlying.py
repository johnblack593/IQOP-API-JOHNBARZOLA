"""Test get_digital_underlying to find Digital assets."""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.ERROR)

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect(ssid=SSID)
time.sleep(2)

def test_digital_underlying():
    print("\nRequesting Digital Underlying List...")
    api.api.underlying_list_data = None
    api.api.underlying_list_data_event.clear()
    api.api.get_digital_underlying()
    
    start_t = time.time()
    while time.time() - start_t < 10:
        if api.api.underlying_list_data:
            print("Response received!")
            with open('scratch/digital_underlying.json', 'w') as f:
                json.dump(api.api.underlying_list_data, f, indent=2)
            print(f"Underlying assets count: {len(api.api.underlying_list_data.get('underlying', []))}")
            return
        time.sleep(0.5)
    print("Timeout waiting for underlying list.")

test_digital_underlying()
api.close()
