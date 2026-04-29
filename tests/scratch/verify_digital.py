"""Verify Digital buy with updated stable_api logic."""
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

print("\n=== TEST: buy_digital_spot_v2(EURUSD-OTC, 1, call, 1) ===")
# stable_api should now handle the -OTC removal internally
success, order_id = api.buy_digital_spot_v2("EURUSD-OTC", 1, "call", 1)
print(f"Result: success={success}, order_id={order_id}")

if success and order_id:
    print("\nDIGITAL CERTIFICATION: PASS")
else:
    print("\nDIGITAL CERTIFICATION: FAIL")

api.close()
