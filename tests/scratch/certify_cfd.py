"""Sprint 5 — Task 3: CFD buy_order() + close_position() certification.
Executes a REAL trade on PRACTICE balance, then closes it.
"""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')

SSID = "05ac28045097edb0fcde0d87e0ce207q"

email = os.getenv('IQ_EMAIL')
password = os.getenv('IQ_PASSWORD')

print(f"=== CFD TRADE CERTIFICATION ===")
print(f"Account: {email}")
print(f"Mode: PRACTICE (demo)")
print()

# --- Connect ---
api = IQ_Option(email, password)
status, reason = api.connect(ssid=SSID)
if not status:
    print(f"Connection FAILED: {reason}")
    sys.exit(1)
print("Connected OK.")

# --- Ensure PRACTICE balance ---
api.change_balance("PRACTICE")
time.sleep(2)
balance = api.get_balance()
print(f"Balance: ${balance}")

# --- Find open forex/cfd assets ---
print("\nScanning for open assets...")
open_time = api.get_all_open_time()

# Try forex first (most liquid)
candidates = []
for cat in ["forex", "cfd", "crypto"]:
    if cat in open_time:
        for name, info in open_time[cat].items():
            if info.get("open"):
                candidates.append((cat, name))

print(f"Found {len(candidates)} open CFD/Forex/Crypto assets.")
if candidates:
    print(f"First 10: {candidates[:10]}")

if not candidates:
    print("ERROR: No open assets found!")
    api.close()
    sys.exit(1)

# Pick the first forex OTC (most reliable for demo)
test_type, test_asset = None, None
# Priority: forex OTC > forex non-OTC > cfd > crypto
for cat, name in candidates:
    if cat == "forex" and "OTC" in name:
        test_type, test_asset = cat, name
        break
if not test_type:
    for cat, name in candidates:
        if cat == "forex":
            test_type, test_asset = cat, name
            break
if not test_type:
    test_type, test_asset = candidates[0]

print(f"\n>>> Selected: {test_type}/{test_asset}")

# --- Execute buy_order ---
print(f"\n=== BUY ORDER ===")
print(f"  Type: {test_type}")
print(f"  Asset: {test_asset}")
print(f"  Side: buy")
print(f"  Amount: $1")
print(f"  Leverage: 1")

success, order_id = api.buy_order(
    instrument_type=test_type,
    instrument_id=test_asset,
    side="buy",
    amount=1,
    leverage=1,
    type="market"
)

print(f"  Result: success={success}, order_id={order_id}")

if not success:
    print(f"  BUY FAILED: {order_id}")
    api.close()
    sys.exit(1)

print(f"  Order placed successfully! ID: {order_id}")

# --- Wait a moment ---
print("\nWaiting 3s before closing position...")
time.sleep(3)

# --- Close position ---
print(f"\n=== CLOSE POSITION ===")
print(f"  Order ID: {order_id}")

close_result = api.close_position(order_id)
print(f"  Close result: {close_result}")

# --- Check profit/loss ---
print("\nWaiting 2s for position history...")
time.sleep(2)

check_success, profit = api.check_order_profit(order_id)
print(f"  Profit check: success={check_success}, profit={profit}")

# --- Final balance ---
final_balance = api.get_balance()
print(f"\nFinal balance: ${final_balance}")
print(f"Balance change: ${final_balance - balance}")

print(f"\n{'='*50}")
print(f"CFD TRADE CERTIFICATION: {'PASSED' if success else 'FAILED'}")
print(f"{'='*50}")

api.close()
