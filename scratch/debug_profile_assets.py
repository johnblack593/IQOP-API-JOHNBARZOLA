import os
import time
import threading
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

iq = IQ_Option(email, password)
check, reason = iq.connect()
if not check:
    print(f"FAIL: {reason}")
    exit(1)

print("OK Connected")

profile = iq.get_profile_ansyc()
print("Profile keys:", profile.keys() if profile else "None")
if profile and "balances" in profile:
    print("Balances count:", len(profile["balances"]))
    for b in profile["balances"]:
        print(f"  Type: {b['type']}, ID: {b['id']}, Amount: {b['amount']}, Currency: {b.get('currency')}")

print("Current balance_id in api:", iq.api.balance_id)

print("\nAttempting change_balance('PRACTICE')...")
try:
    iq.change_balance("PRACTICE")
    print("New balance_id:", iq.api.balance_id)
except Exception as e:
    print(f"FAIL change_balance: {e}")

print("\nChecking assets...")
data = iq.get_all_init_v2()
print("Init V2 keys:", data.keys() if data else "None")
if data:
    for k in ["binary", "turbo", "digital", "blitz", "forex", "cfd", "crypto"]:
        if k in data:
            count = len(data[k].get("actives", {}))
            print(f"  {k} actives: {count}")
        else:
            print(f"  {k} MISSING")

assets = iq.get_all_open_time()
# Check turbo assets
turbo = assets.get("turbo", {})
open_turbo = [k for k, v in turbo.items() if v.get("open")]
print(f"Open Turbo assets: {len(open_turbo)}")
if open_turbo:
    print(f"  Sample: {open_turbo[:5]}")

iq.api.close()
