"""List digital instruments via get_instruments."""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
status, reason = api.connect(ssid=SSID)
if not status:
    print(f"FAIL: {reason}")
    sys.exit(1)

api.change_balance("PRACTICE")
time.sleep(3)

print("Fetching digital instruments via get_instruments...")
# This uses the standard instruments endpoint
data = api.get_instruments("digital")
with open('scratch/digital_catalog.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Found {len(data) if data else 0} digital instruments.")
if data and len(data) > 0:
    print("Example instrument_id pattern:")
    # Look for one with a recognizable ID
    for item in data:
        print(f"  {item.get('id')} - {item.get('name')}")
        break

api.close()
