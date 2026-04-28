import os
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv
import json

load_dotenv()

def check_digital_assets():
    api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
    SSID = "05ac28045097edb0fcde0d87e0ce207q"
    status, reason = api.connect(ssid=SSID)
    
    if not status:
        print(f"Connection failed: {reason}")
        return

    print("Fetching initialization data...")
    init_data = api.get_all_init_v2()
    
    digital = init_data.get("digital", {})
    actives = digital.get("actives", {})
    
    print(f"Digital actives count: {len(actives)}")
    for active_id, data in actives.items():
        print(f"ID: {active_id}, Name: {data.get('name')}")
        
    api.close()

if __name__ == "__main__":
    check_digital_assets()
