import os
import time
import json
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

def dump_underlying():
    load_dotenv()
    api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
    api.connect()
    
    print("Fetching digital underlying list...")
    data = api.get_digital_underlying_list_data()
    print(json.dumps(data, indent=2))
    
    api.api.close()

if __name__ == "__main__":
    dump_underlying()
