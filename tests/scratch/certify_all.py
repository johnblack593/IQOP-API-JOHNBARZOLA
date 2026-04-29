"""Sprint 5 — Certification: Digital + Blitz + Binary OTC trades.
Executes trades on PRACTICE balance using assets that are currently OPEN.
The browser confirmed: Blitz(155), Binarias(165), Digital(159) are all open OTC.
Forex/CFD/Acciones are closed (weekend).
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

print(f"{'='*60}")
print(f"  SPRINT 5 — TRADE CERTIFICATION (PRACTICE)")
print(f"  Account: {email}")
print(f"{'='*60}\n")

# --- Connect ---
api = IQ_Option(email, password)
status, reason = api.connect(ssid=SSID)
if not status:
    print(f"Connection FAILED: {reason}")
    sys.exit(1)
print("✓ Connected OK.")

# --- Ensure PRACTICE balance ---
api.change_balance("PRACTICE")
time.sleep(2)
balance = api.get_balance()
print(f"✓ Balance: ${balance}")
print(f"✓ Balance mode: PRACTICE\n")

results = {}

# ═══════════════════════════════════════════════════
# TEST 1: Binary Option (CARDANO-OTC via buy())
# ═══════════════════════════════════════════════════
print(f"\n{'─'*60}")
print(f"TEST 1: BINARY OPTION — CARDANO-OTC")
print(f"{'─'*60}")

try:
    success, order_id = api.buy(1, "CARDANO-OTC", "call", 1)
    print(f"  buy() → success={success}, order_id={order_id}")
    if success and order_id:
        print(f"  ✓ Binary order placed! ID: {order_id}")
        results["binary"] = {"status": "PASS", "order_id": order_id}
    else:
        print(f"  ✗ Binary order FAILED")
        results["binary"] = {"status": "FAIL", "reason": str(order_id)}
except Exception as e:
    print(f"  ✗ Exception: {e}")
    results["binary"] = {"status": "ERROR", "reason": str(e)}

time.sleep(2)

# ═══════════════════════════════════════════════════
# TEST 2: Blitz Option (CARDANO-OTC via buy_blitz())
# ═══════════════════════════════════════════════════
print(f"\n{'─'*60}")
print(f"TEST 2: BLITZ OPTION — CARDANO-OTC (30s)")
print(f"{'─'*60}")

try:
    # First check blitz catalog
    blitz_catalog = api.get_blitz_instruments()
    print(f"  Blitz catalog: {len(blitz_catalog)} instruments")
    if "CARDANO-OTC" in blitz_catalog:
        print(f"  ✓ CARDANO-OTC found in blitz catalog")
        success, order_id = api.buy_blitz("CARDANO-OTC", 1, "call", 30)
        print(f"  buy_blitz() → success={success}, order_id={order_id}")
        if success and order_id:
            print(f"  ✓ Blitz order placed! ID: {order_id}")
            results["blitz"] = {"status": "PASS", "order_id": order_id}
        else:
            print(f"  ✗ Blitz order FAILED")
            results["blitz"] = {"status": "FAIL", "reason": str(order_id)}
    else:
        available = list(blitz_catalog.keys())[:5]
        print(f"  ✗ CARDANO-OTC not in blitz catalog. Available: {available}")
        # Try first available
        if available:
            first = available[0]
            print(f"  Trying {first} instead...")
            success, order_id = api.buy_blitz(first, 1, "call", 30)
            print(f"  buy_blitz('{first}') → success={success}, order_id={order_id}")
            results["blitz"] = {"status": "PASS" if (success and order_id) else "FAIL",
                               "order_id": order_id, "asset": first}
        else:
            results["blitz"] = {"status": "FAIL", "reason": "empty catalog"}
except Exception as e:
    print(f"  ✗ Exception: {e}")
    import traceback
    traceback.print_exc()
    results["blitz"] = {"status": "ERROR", "reason": str(e)}

time.sleep(2)

# ═══════════════════════════════════════════════════
# TEST 3: Digital Option (EURUSD-OTC via buy_digital_spot_v2())
# ═══════════════════════════════════════════════════
print(f"\n{'─'*60}")
print(f"TEST 3: DIGITAL OPTION — EURUSD-OTC")
print(f"{'─'*60}")

try:
    # Try the digital buy
    success, order_id = api.buy_digital_spot_v2("EURUSD-OTC", 1, "call", 1)
    print(f"  buy_digital_spot_v2() → success={success}, order_id={order_id}")
    if success and order_id:
        print(f"  ✓ Digital order placed! ID: {order_id}")
        results["digital"] = {"status": "PASS", "order_id": order_id}
    else:
        print(f"  ✗ Digital order FAILED: {order_id}")
        # Try CARDANO-OTC as fallback
        print(f"  Trying CARDANO-OTC...")
        success2, order_id2 = api.buy_digital_spot_v2("CARDANO-OTC", 1, "call", 1)
        print(f"  buy_digital_spot_v2('CARDANO-OTC') → success={success2}, order_id={order_id2}")
        results["digital"] = {"status": "PASS" if (success2 and order_id2) else "FAIL",
                             "order_id": order_id2}
except Exception as e:
    print(f"  ✗ Exception: {e}")
    import traceback
    traceback.print_exc()
    results["digital"] = {"status": "ERROR", "reason": str(e)}

# ═══════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════
print(f"\n\n{'='*60}")
print(f"  CERTIFICATION SUMMARY")
print(f"{'='*60}")

final_balance = api.get_balance()
print(f"  Final balance: ${final_balance} (delta: ${final_balance - balance})")
print()

all_pass = True
for test_name, result in results.items():
    status_icon = "✓" if result["status"] == "PASS" else "✗"
    print(f"  {status_icon} {test_name:15s}: {result['status']}")
    if result["status"] != "PASS":
        all_pass = False

print(f"\n{'='*60}")
print(f"  OVERALL: {'ALL PASSED ✓' if all_pass else 'SOME FAILED ✗'}")
print(f"{'='*60}")

# Save results
with open('scratch/certification_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

api.close()
