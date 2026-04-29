"""Test: Send get-initialization-data v3.0 to see if blitz/digital appear."""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
status, reason = api.connect(ssid=SSID)
if not status:
    print(f"FAIL: {reason}")
    sys.exit(1)

time.sleep(3)

# Send v3.0 of get-initialization-data
print("Sending get-initialization-data v3.0...")
msg = {
    "name": "get-initialization-data",
    "version": "3.0",
    "body": {}
}
api.api.send_websocket_request(name="sendMessage", msg=msg)

# Wait for the response
print("Waiting 10s for response...")
time.sleep(10)

# Check what we got
init_v2 = api.api.api_option_init_all_result_v2
if init_v2:
    print("\n=== INIT V2 (from v3 request) ===")
    for k in sorted(init_v2.keys()):
        v = init_v2[k]
        if isinstance(v, dict) and "actives" in v:
            actives = v["actives"]
            open_count = sum(1 for a in actives.values() 
                            if a.get("enabled") and not a.get("is_suspended"))
            print(f"  {k:15s}: {len(actives):4d} total, {open_count:4d} open")
        elif isinstance(v, dict):
            print(f"  {k:15s}: dict keys={list(v.keys())[:5]}")
        elif isinstance(v, list):
            print(f"  {k:15s}: list len={len(v)}")
        else:
            print(f"  {k:15s}: {type(v).__name__} = {str(v)[:80]}")
    
    # Check blitz specifically
    blitz = init_v2.get("blitz", {})
    blitz_actives = blitz.get("actives", {})
    if blitz_actives:
        print(f"\n=== BLITZ ACTIVES (first 5) ===")
        for aid, data in list(blitz_actives.items())[:5]:
            print(f"  {aid}: {data.get('name')}, enabled={data.get('enabled')}")
    
    # Check digital
    digital = init_v2.get("digital", {})
    digital_actives = digital.get("actives", {})
    if digital_actives:
        print(f"\n=== DIGITAL ACTIVES (first 5) ===")
        for aid, data in list(digital_actives.items())[:5]:
            print(f"  {aid}: {data.get('name')}, enabled={data.get('enabled')}")
            
    # Save
    with open('tests/fixtures/init_v3_data.json', 'w') as f:
        json.dump(init_v2, f, indent=2)
    print("\nSaved to tests/fixtures/init_v3_data.json")
else:
    print("init_v2 is STILL None after v3 request!")

# Also check blitz_instruments
blitz_inst = getattr(api.api, 'blitz_instruments', {})
print(f"\napi.blitz_instruments: {len(blitz_inst)} instruments")
if blitz_inst:
    for name, data in list(blitz_inst.items())[:5]:
        print(f"  {name}: id={data.get('id')}, open={data.get('open')}")

api.close()
