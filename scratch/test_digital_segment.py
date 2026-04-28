"""Test get-initialization-data v3.0 with segment='digital'."""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect(ssid=SSID)
time.sleep(2)

def get_digital_init():
    print("\nRequesting Digital Init Segment...")
    msg = {
        "name": "get-initialization-data",
        "version": "3.0",
        "body": {"segment": "digital"}
    }
    api.api.api_option_init_all_result_v2 = None
    api.api.api_option_init_all_result_v2_event.clear()
    api.api.send_websocket_request(name="sendMessage", msg=msg)
    
    if api.api.api_option_init_all_result_v2_event.wait(timeout=10):
        data = api.api.api_option_init_all_result_v2
        print(f"Received segment keys: {list(data.keys())}")
        if "digital" in data:
            print(f"Digital assets found: {len(data['digital'].get('actives', {}))}")
            with open('scratch/digital_segment.json', 'w') as f:
                json.dump(data, f, indent=2)
        else:
            print("Digital key NOT found in response.")
    else:
        print("Timeout waiting for response.")

get_digital_init()
api.close()
