from iqoptionapi.stable_api import IQ_Option
import os
import time
from dotenv import load_dotenv

load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()
api.change_balance('PRACTICE')

print("Balance Inicial:", api.get_balance())

# Buy a turbo option
print("Placing 1 USD Turbo Call on US2000-OTC...")
success, id_number = api.buy(1, "US2000-OTC", "call", 1)

if success:
    print(f"Trade placed successfully. Order ID: {id_number}")
    print("Waiting for result using _wait_result (up to 120 seconds)...")
    start = time.time()
    result = api._wait_result(id_number, api.listinfodata, api.result_event_store, timeout=120.0)
    print(f"_wait_result listinfodata returned: {result} after {time.time() - start:.2f} seconds")
    
    result3 = api._wait_result(id_number, api.socket_option_closed, api.socket_option_closed_event, timeout=1.0)
    print(f"_wait_result socket_option_closed returned: {result3}")
    print(f"check_win_v3 returned: {result} after {time.time() - start:.2f} seconds")
    
    # We can't check_win_v2 for the same order since the event might have already fired and been deleted, 
    # but check_win_v3 relies on socket_option_closed which we modified listinfodata to match.
    # We will test check_win_v2 specifically:
    print("Testing check_win_v2 without timeout crash...")
    res2 = api.check_win_v2(id_number, timeout=1.0)
    print(f"check_win_v2 returned: {res2}")
else:
    print("Failed to place trade.")
