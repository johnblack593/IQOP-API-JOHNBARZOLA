"""Subscribe to digital option quotes with correct arguments."""
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
    print("\nSubscribing to Digital Quotes for EURUSD-OTC (1m period)...")
    # second arg is period in minutes
    api.api.subscribe_instrument_quotes_generated("EURUSD-OTC", 1)
    
    print("Waiting 15 seconds for quotes...")
    start_t = time.time()
    while time.time() - start_t < 15:
        if api.api.instrument_quotes_generated_data:
            print("Quotes received!")
            for active_id, quotes in api.api.instrument_quotes_generated_data.items():
                print(f"Active ID: {active_id}")
                for q in quotes.get('quotes', []):
                    # q['symbols'][0] is the instrument_id
                    print(f"  Instrument ID: {q.get('symbols')[0] if q.get('symbols') else 'N/A'}")
                    # Print one full quote for structure
                    print(json.dumps(q, indent=2))
                    return # Exit after one
            break
        time.sleep(0.5)
    
    api.api.unsubscribe_instrument_quotes_generated("EURUSD-OTC", 1)

test_digital_quotes()
api.close()
