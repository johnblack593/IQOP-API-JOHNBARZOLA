"""Subscribe to digital quotes and print nested data."""
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
    api.api.subscribe_instrument_quotes_generated("EURUSD-OTC", 1)
    
    print("Waiting 15 seconds for quotes...")
    start_t = time.time()
    while time.time() - start_t < 15:
        data = api.api.instrument_quotes_generated_data
        if "EURUSD-OTC" in data and len(data["EURUSD-OTC"]) > 0:
            print("Quotes received in nested dict!")
            print(json.dumps(data["EURUSD-OTC"], indent=2))
            return
        time.sleep(0.5)
    
    print("FAILED: No quotes received.")
    api.api.unsubscribe_instrument_quotes_generated("EURUSD-OTC", 1)

test_digital_quotes()
api.close()
