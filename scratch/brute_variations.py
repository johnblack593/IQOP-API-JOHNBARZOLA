import os
import json
import time
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()

api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()

balance_id = api.get_balance_id()
active_id = 76
asset_name = "EURUSD-OTC"

variations = [
    f"digital-option.{asset_name}.PT1M",
    f"digital-option.{asset_name}.PT1MCSPT",
    f"{asset_name}.PT1M",
    f"do{asset_name}.PT1M",
    f"digital-{asset_name}-1M",
]

for inst_id in variations:
    print(f"\n--- Trying {inst_id} ---")
    payload = {
        "name": "digital-options.place-digital-option",
        "version": "2.0",
        "body": {
            "amount": "1",
            "asset_id": active_id,
            "instrument_id": inst_id,
            "instrument_index": 0,
            "user_balance_id": balance_id
        }
    }
    api.api.send_websocket_request(name="sendMessage", msg=payload)
    time.sleep(2)

api.api.close()
