import os
import json
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.ws.client import WebsocketClient

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

# HOOK WebsocketClient.on_message GLOBALLY before connect
raw_messages = []
original_on_message = WebsocketClient.on_message

def capturing_on_message(self, wss, message):
    try:
        parsed = json.loads(message)
        name = parsed.get("name", "UNNAMED")
        # Log to list
        raw_messages.append(parsed)
    except:
        pass
    return original_on_message(self, wss, message)

WebsocketClient.on_message = capturing_on_message

print(f"Connecting with email: {email}")
api = IQ_Option(email, password)
api.connect()
api.change_balance("PRACTICE")

# 1. Dump completo de open_time
open_times = api.get_all_open_time()
with open("examples/debug_open_time.json", "w") as f:
    json.dump(open_times, f, indent=2)

# 2. Dump de instruments
categories = ["binary-option", "blitz", "turbo-option", "digital-option", "fx-option"]
for category in categories:
    try:
        result = api.get_instruments(category)
        with open(f"examples/debug_instruments_{category}.json", "w") as f:
            json.dump(result, f, indent=2)
    except:
        pass

# 3. Capture more messages
print("Capturing more WS messages for 10 seconds...")
time.sleep(10)

with open("examples/debug_ws_messages.json", "w") as f:
    json.dump(raw_messages, f, indent=2)

unique_names = list(set([m.get("name") for m in raw_messages if isinstance(m, dict)]))
print(f"WS messages captured: {len(raw_messages)}")
print(f"Unique names: {unique_names}")

api.close()
