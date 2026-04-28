"""Quick test: binary buy() with 1min duration (turbo) to verify it works."""
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

balance = api.get_balance()
print(f"Balance: ${balance}")

# Test 1: buy() with 1 min (turbo)
print("\n=== TEST: buy(1, CARDANO-OTC, call, 1) ===")
success, order_id = api.buy(1, "CARDANO-OTC", "call", 1)
print(f"  Result: success={success}, order_id={order_id}")

time.sleep(1)
balance2 = api.get_balance()
print(f"  Balance: ${balance2} (delta: ${balance2 - balance})")

if success and order_id:
    print(f"\n  TURBO/BINARY 1min: PASS")
else:
    print(f"\n  TURBO/BINARY 1min: FAIL")

api.close()
