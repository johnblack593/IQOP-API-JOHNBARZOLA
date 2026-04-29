import os
import time
import json
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

def dump_underlying():
    load_dotenv()
    api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
    api.connect()
    
    print("Fetching underlying list...")
    api.get_digital_underlying_list_data()
    
    # Wait for data
    for _ in range(10):
        if api.api.underlying_list_data is not None:
            break
        time.sleep(1)
    
    if api.api.underlying_list_data:
        print(json.dumps(api.api.underlying_list_data, indent=2))
    else:
        print("Failed to fetch underlying list.")
    
    api.api.close()

if __name__ == "__main__":
    dump_underlying()
