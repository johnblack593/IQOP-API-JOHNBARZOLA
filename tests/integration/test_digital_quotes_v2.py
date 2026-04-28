"""Subscribe to digital option quotes using the correct asset name."""
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
    print("\nSubscribing to Digital Quotes for EURUSD-OTC...")
    # Pass the string name
    api.api.subscribe_instrument_quotes_generated("EURUSD-OTC", "digital-option")
    
    print("Waiting 10 seconds for quotes...")
    start_t = time.time()
    while time.time() - start_t < 10:
        if api.api.instrument_quotes_generated_data:
            print("Quotes received!")
            # The data is a dict
            # We want to see the keys, which are likely the instrument IDs
            for active_id, quotes in api.api.instrument_quotes_generated_data.items():
                print(f"Active ID: {active_id}")
                # quotes['quotes'] is a list of instrument quotes
                for q in quotes.get('quotes', []):
                    print(f"  Instrument ID: {q.get('symbols')[0] if q.get('symbols') else 'N/A'}")
                    # Print one full quote for structure
                    print(json.dumps(q, indent=2))
                    break
                break
            break
        time.sleep(0.5)
    
    api.api.unsubscribe_instrument_quotes_generated("EURUSD-OTC", "digital-option")

test_digital_quotes()
api.close()
