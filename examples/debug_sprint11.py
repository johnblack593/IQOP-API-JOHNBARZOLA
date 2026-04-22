import os, sys, json, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tests.practice_suite.config import IQ_EMAIL, IQ_PASSWORD
from iqoptionapi.stable_api import IQ_Option
api = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
check, msg = api.connect()
if not check:
    print(f"FAILED TO CONNECT: {msg}")
    sys.exit(1)
api.change_balance("PRACTICE")

print("\n--- REVERSE ENGINEERING ---")
binary_data = api.get_all_init_v2()
print("all_init_v2 keys:", list(binary_data.keys()) if isinstance(binary_data, dict) else type(binary_data))

if hasattr(api.api, 'api_option_init_all_result') and isinstance(api.api.api_option_init_all_result, dict):
    print("Inner init result keys:", list(api.api.api_option_init_all_result.keys()))

print("Has blitz_instruments?", hasattr(api.api, 'blitz_instruments'))
if hasattr(api.api, 'blitz_instruments') and isinstance(api.api.blitz_instruments, dict):
    print("Sample blitz:", list(api.api.blitz_instruments.keys())[:5])

api.close()
