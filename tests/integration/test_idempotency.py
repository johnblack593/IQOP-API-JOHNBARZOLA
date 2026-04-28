import os
import threading
from collections import defaultdict
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

def test_idempotency():
    load_dotenv()
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    
    iq = IQ_Option(email, password)
    
    print("Initial connect...")
    iq.connect()
    
    # Simulate some data in stores
    iq.api.result_event_store[123] = threading.Event()
    iq.api.socket_option_closed_event[456] = threading.Event()
    print(f"Store size before second connect: {len(iq.api.result_event_store)}")
    
    print("Second connect...")
    iq.connect()
    
    print(f"Store size after second connect: {len(iq.api.result_event_store)}")
    
    if len(iq.api.result_event_store) == 0:
        print("SUCCESS: Connect is idempotent and clears stores.")
    else:
        print("FAILURE: Connect did not clear stores.")
    
    iq.api.close()

if __name__ == "__main__":
    test_idempotency()
