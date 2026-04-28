import os
import json
import time
import websocket
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()

api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()

balance_id = api.get_balance_id()
print(f"Balance ID: {balance_id}")

# Use the ID we found
active_id = 76
asset_name = "EURUSD-OTC"

# Try v1.0 first (simpler)
print("\n--- Trying v1.0 ---")
# Format: digital-option.{asset}.{duration}{type}{strike_type}
# But we'll try a few variations
instrument_id = f"digital-option.{asset_name}.PT1MCSPT"
print(f"Instrument ID: {instrument_id}")

payload = {
    "name": "digital-options.place-digital-option",
    "version": "1.0",
    "body": {
        "user_balance_id": balance_id,
        "instrument_id": instrument_id,
        "amount": "1"
    }
}
api.api.send_websocket_request(name="sendMessage", msg=payload)
time.sleep(5)

# Try v2.0
print("\n--- Trying v2.0 ---")
payload_v2 = {
    "name": "digital-options.place-digital-option",
    "version": "2.0",
    "body": {
        "amount": "1",
        "asset_id": active_id,
        "instrument_id": instrument_id,
        "instrument_index": 0,
        "user_balance_id": balance_id
    }
}
api.api.send_websocket_request(name="sendMessage", msg=payload_v2)
time.sleep(5)

api.api.close()
