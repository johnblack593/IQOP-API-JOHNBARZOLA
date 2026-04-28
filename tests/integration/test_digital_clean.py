"""Test: Digital buy with corrected instrument_id (no -OTC)."""
import os, sys, json, time, logging
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.expiration import get_expiration_time
from iqoptionapi.constants import ACTIVES
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
    if not active_id:
        print(f"Error: {active} not in ACTIVES")
        return

    timestamp = int(api.api.timesync.server_timestamp)
    exp, _ = get_expiration_time(timestamp, duration)
    date_formated = str(datetime.utcfromtimestamp(exp).strftime("%Y%m%d%H%M"))
    
    # Try WITHOUT -OTC
    clean_active = active.replace("-OTC", "")
    instrument_id = "do" + clean_active + date_formated + "PT" + str(duration) + "M" + action + "SPT"
    
    print(f"Generated Instrument ID: {instrument_id}")
    
    api.api.digital_option_placed_id = None
    api.api.place_digital_option_v2(instrument_id, active_id, amount)
    
    start_t = time.time()
    while time.time() - start_t < 10:
        if api.api.digital_option_placed_id:
            print(f"SUCCESS! Digital Order ID: {api.api.digital_option_placed_id}")
            return True
        time.sleep(0.5)
    
    print("FAILED: Timeout or rejected")
    return False

# Test with EURUSD-OTC but clean ID
test_digital_buy("EURUSD-OTC", 1, "call", 1)
# Also try with CARDANO-OTC
test_digital_buy("CARDANO-OTC", 1, "call", 1)

api.close()
