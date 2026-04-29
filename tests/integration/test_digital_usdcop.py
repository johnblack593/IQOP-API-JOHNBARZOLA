"""Test: Digital buy with USDCOP to match subagent discovery."""
import os, sys, json, time, logging
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.expiration import get_expiration_time
from iqoptionapi.core.constants import ACTIVES
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

def test_digital_buy(active, duration, action, amount):
    print(f"\n--- Testing Digital Buy for {active} ---")
    active_id = ACTIVES.get(active)
    
    timestamp = int(api.api.timesync.server_timestamp)
    exp, _ = get_expiration_time(timestamp, duration)
    # The subagent found 23:19 when local was 22:57. 
    # Let's see what get_expiration_time gives us.
    date_formated = str(datetime.fromtimestamp(exp).strftime("%Y%m%d%H%M"))
    
    clean_active = active.replace("-OTC", "").replace("/", "")
    action_letter = "C" if action.lower() == "call" else "P"
    instrument_id = "do" + clean_active + date_formated + "PT" + str(duration) + "M" + action_letter + "SPT"
    
    print(f"Server Timestamp: {timestamp}")
    print(f"Expiration: {exp} (Local: {datetime.fromtimestamp(exp)})")
    print(f"Generated Instrument ID: {instrument_id}")
    
    api.api.digital_option_placed_id = {}
    api.api.place_digital_option_v2(instrument_id, active_id, amount)
    
    start_t = time.time()
    while time.time() - start_t < 10:
        if api.api.digital_option_placed_id:
            req_id = list(api.api.digital_option_placed_id.keys())[0]
            res = api.api.digital_option_placed_id[req_id]
            if isinstance(res, int):
                print(f"SUCCESS! Digital Order ID: {res}")
                return True
            else:
                print(f"REJECTED: {res}")
                return False
        time.sleep(0.5)
    
    print("FAILED: Timeout")
    return False

# Try USDCOP-OTC
test_digital_buy("USDCOP-OTC", 1, "call", 1)

api.close()

