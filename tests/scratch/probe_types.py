"""List all instrument types available via get_instruments."""
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

types = ["binary", "turbo", "digital", "digital-option", "blitz", "forex", "cfd", "crypto", "indices", "stocks", "commodities", "etf"]
results = {}

for t in types:
    print(f"Checking type: {t}")
    try:
        # We need to use a request_id and wait for response
        data = api.get_instruments(t)
        results[t] = len(data) if data else 0
    except Exception as e:
        results[t] = f"Error: {str(e)}"

print("\nResults:")
print(json.dumps(results, indent=2))

api.close()
