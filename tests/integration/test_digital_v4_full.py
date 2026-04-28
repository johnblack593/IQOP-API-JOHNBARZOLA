"""Test get-instruments v4.0 and print full response."""
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
    api.api.instruments = None
    api.api.instruments_event.clear()
    api.api.send_websocket_request(name="sendMessage", msg=msg)
    
    start_t = time.time()
    while time.time() - start_t < 10:
        if api.api.instruments:
            print("Response received:")
            print(json.dumps(api.api.instruments, indent=2))
            return
        time.sleep(0.5)
    print("Timeout waiting for instruments.")

get_digital_instruments_v4()
api.close()
