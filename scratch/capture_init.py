import os
import json
import time
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()

email = os.getenv('IQ_EMAIL')
password = os.getenv('IQ_PASSWORD')

print(f"Connecting with {email}...")
api = IQ_Option(email, password)
status, reason = api.connect()

if not status:
    print(f"Connection failed: {reason}")
    exit(1)

print("Connected. Waiting for initialization data...")
time.sleep(5)

# Save debug_init.json
print("Saving debug_init.json...")
with open('debug_init.json', 'w') as f:
    json.dump(api.api.api_option_init_all_result, f, indent=2)

# Save open_time.json
print("Auditing catalog (get_all_open_time)...")
open_time = api.get_all_open_time()
with open('open_time.json', 'w') as f:
    json.dump(open_time, f, indent=2)

# Save digital_underlying.json
print("Saving digital_underlying.json...")
underlying = api.get_digital_underlying_list_data()
with open('digital_underlying.json', 'w') as f:
    json.dump(underlying, f, indent=2)

print("Done. Generated debug_init.json, open_time.json and digital_underlying.json")
api.close()
