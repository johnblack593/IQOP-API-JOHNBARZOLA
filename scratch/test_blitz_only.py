"""Test ONLY blitz buy in isolation to debug order_id capture."""
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

balance_before = api.get_balance()
print(f"Balance before: ${balance_before}")
print(f"Blitz catalog: {len(api.api.blitz_instruments)} instruments")
print(f"pending_buy_ids before: {list(api.api.pending_buy_ids)}")
print(f"buy_multi_option before: {api.api.buy_multi_option}")

print(f"\n=== BUY_BLITZ CARDANO-OTC 30s call ===")
success, order_id = api.buy_blitz("CARDANO-OTC", 1, "call", 30)
print(f"Result: success={success}, order_id={order_id}")
print(f"pending_buy_ids after: {list(api.api.pending_buy_ids)}")
print(f"buy_multi_option after: {json.dumps(api.api.buy_multi_option, default=str)}")

time.sleep(2)
balance_after = api.get_balance()
print(f"\nBalance after: ${balance_after} (delta: ${balance_after - balance_before})")

if order_id:
    print(f"\nBLITZ CERTIFICATION: PASS (order_id={order_id})")
elif balance_after < balance_before:
    print(f"\nBLITZ: Order was placed (balance dropped) but order_id not captured")
else:
    print(f"\nBLITZ CERTIFICATION: FAIL")

api.close()
