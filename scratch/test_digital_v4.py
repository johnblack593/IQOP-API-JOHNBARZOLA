"""Test get-instruments v4.0 with type='digital-option'."""
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

def get_digital_instruments_v4():
    print("\nRequesting Digital Instruments v4.0...")
    msg = {
        "name": "get-instruments",
        "version": "4.0",
        "body": {"type": "digital-option"}
    }
    # We use result_event since it's a generic response usually
    api.api.result = None
    api.api.result_event.clear()
    api.api.send_websocket_request(name="sendMessage", msg=msg)
    
    # We might need to check if there is a specific handler for 'instruments' name
    # In client.py, 'instruments' maps to instruments.py handler.
    # That handler sets api.instruments and api.instruments_event.
    api.api.instruments = None
    api.api.instruments_event.clear()
    
    start_t = time.time()
    while time.time() - start_t < 10:
        if api.api.instruments:
            print(f"Received instruments! Keys: {list(api.api.instruments.keys())}")
            if "instruments" in api.api.instruments:
                print(f"Count: {len(api.api.instruments['instruments'])}")
                with open('scratch/digital_instruments_v4.json', 'w') as f:
                    json.dump(api.api.instruments, f, indent=2)
            return
        time.sleep(0.5)
    print("Timeout waiting for instruments.")

get_digital_instruments_v4()
api.close()
