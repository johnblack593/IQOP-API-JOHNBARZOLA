"""Capture all incoming initialization-data keys to see if it arrives in segments."""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
# Set logging to INFO to see our new logs in initialization_data.py
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
status, reason = api.connect(ssid=SSID)
if not status:
    print(f"FAIL: {reason}")
    sys.exit(1)

api.change_balance("PRACTICE")
time.sleep(2)

print("\nTriggering get_all_init_v2 (v3.0 request)...")
# We clear the cache to force a new request
api.api.api_option_init_all_result_v2 = None
api.get_all_init_v2()

print("\nWaiting 10 seconds for any potential delayed segments...")
time.sleep(10)

print("\nFinal keys in api_option_init_all_result_v2:")
if api.api.api_option_init_all_result_v2:
    print(list(api.api.api_option_init_all_result_v2.keys()))
else:
    print("None")

api.close()
