import os
import json
import time
import websocket
websocket.enableTrace(True)
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()

api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()

balance_id = api.get_balance_id()
print(f"Balance ID: {balance_id}")

formats = [
    "digital-option.EURUSD-OTC.PT1M",
    "digital-option.EURUSD-OTC.PT1MCSPT",
    "digital-option.EURUSD-OTC.PT1MPSPT",
    "doEURUSD-OTC.PT1M",
    "doEURUSD-OTC.PT1MCSPT",
    "digital-option.EURUSD.PT1M",
    "EURUSD-OTC.PT1M"
]

for fmt in formats:
    print(f"\nTrying format: {fmt}")
    req_id = f"test_{int(time.time())}_{fmt}"
    payload = {
        "name": "digital-options.place-digital-option",
        "version": "2.0",
        "body": {
            "user_balance_id": balance_id,
            "instrument_id": fmt,
            "amount": "1"
        }
    }
    api.api.send_websocket_request(name="sendMessage", msg=payload)
    time.sleep(2)
    # Check for any error in the last received messages
    # This is a bit hard without a custom handler, but we can check if anything was recorded
    # Actually, we can just look at the websocket trace if we run with -v
    
api.api.close()
