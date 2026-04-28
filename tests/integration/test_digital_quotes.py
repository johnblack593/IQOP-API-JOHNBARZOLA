"""Subscribe to digital option quotes to see valid instrument IDs."""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.ERROR)

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect(ssid=SSID)
time.sleep(2)

def test_digital_quotes():
    print("\nSubscribing to Digital Quotes for Active 76 (EURUSD-OTC)...")
    # Active 76 is EURUSD-OTC as found by subagent
    api.api.subscribe_instrument_quotes_generated(76, "digital-option")
    
    print("Waiting 10 seconds for quotes...")
    start_t = time.time()
    while time.time() - start_t < 10:
        if api.api.instrument_quotes_generated_data:
            print("Quotes received!")
            # The data is usually a dict keyed by active_id or instrument_id
            print(json.dumps(api.api.instrument_quotes_generated_data, indent=2))
            break
        time.sleep(0.5)
    
    api.api.unsubscribe_instrument_quotes_generated(76, "digital-option")

test_digital_quotes()
api.close()
