"""
examples/debug_events_map.py
─────────────────────────────
Mide la latencia real de respuesta WS para cada método con spin-loop.
Ejecutar en PRACTICE account antes de migrar spin-loops a Event.wait().
Output: examples/debug_latency_report.json
"""
import os
import json
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
status, reason = api.connect()
if not status:
    print(f"ERROR connect: {reason}")
    exit(1)

api.change_balance("PRACTICE")

report = {}

def timed(name, fn):
    t0 = time.perf_counter()
    result = fn()
    elapsed = round(time.perf_counter() - t0, 3)
    ok = result is not None
    report[name] = {"latency_s": elapsed, "ok": ok}
    status_icon = "[OK]" if ok else "[NO]"
    print(f"  {status_icon} {name}: {elapsed}s — {'OK' if ok else 'None/timeout'}")
    return result

print("\n=== LATENCY REPORT ===")

timed("get_profile",         lambda: api.get_profile_answertime())
timed("get_all_init_v2",     lambda: api.get_all_init_v2())
timed("get_candles_1m",      lambda: api.get_candles("EURUSD", 60, 10, time.time()))
timed("get_digital_underlying", lambda: api.get_digital_underlying_list_data())
timed("reset_practice",      lambda: api.reset_practice_balance())

# get_user_profile_client needs an ID, let's get it from profile
profile = api.get_profile()
if profile and "id" in profile:
    timed("get_user_profile",    lambda: api.get_user_profile_client(profile["id"]))

with open("examples/debug_latency_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"\nReport guardado en examples/debug_latency_report.json")
api.close()
