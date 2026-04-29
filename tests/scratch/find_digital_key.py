"""Search for 'digital' in the whole initialization-data response."""
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

api.api.api_option_init_all_result_v2 = None
api.get_all_init_v2()

data = api.api.api_option_init_all_result_v2
if data:
    dump = json.dumps(data).lower()
    print(f"Contains 'digital': {'digital' in dump}")
    print(f"Contains 'digital-option': {'digital-option' in dump}")
    
    # Check if 'digital' is a key in any sub-dict
    def find_key(d, target):
        if not isinstance(d, dict): return False
        if target in d: return True
        for v in d.values():
            if isinstance(v, (dict, list)):
                if find_key(v, target): return True
        return False
        
    print(f"Key 'digital' exists somewhere: {find_key(data, 'digital')}")
else:
    print("No data received")

api.close()
