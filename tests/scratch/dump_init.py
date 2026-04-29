"""Dump the raw initialization-data keys and blitz/digital sections."""
import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
status, reason = api.connect(ssid=SSID)
if not status:
    print(f"FAIL: {reason}")
    sys.exit(1)

time.sleep(5)

init = api.api.api_option_init_all_result_v2
if init:
    print("=== TOP-LEVEL KEYS ===")
    for k in init.keys():
        v = init[k]
        if isinstance(v, dict) and "actives" in v:
            print(f"  {k}: {len(v['actives'])} actives")
        elif isinstance(v, dict):
            print(f"  {k}: dict with keys {list(v.keys())[:5]}")
        else:
            print(f"  {k}: {type(v).__name__}")

    # Check for blitz specifically
    print("\n=== BLITZ SECTION ===")
    blitz = init.get("blitz", {})
    print(f"  blitz keys: {list(blitz.keys()) if blitz else 'EMPTY'}")
    if blitz and "actives" in blitz:
        print(f"  blitz actives count: {len(blitz['actives'])}")
        # Show first 3
        for aid, data in list(blitz['actives'].items())[:3]:
            print(f"    {aid}: name={data.get('name')}, enabled={data.get('enabled')}")

    # Check for digital specifically
    print("\n=== DIGITAL SECTION ===")
    digital = init.get("digital", {})
    print(f"  digital keys: {list(digital.keys()) if digital else 'EMPTY'}")
    if digital and "actives" in digital:
        print(f"  digital actives count: {len(digital['actives'])}")

    # Check turbo section (blitz might be under turbo)
    print("\n=== TURBO SECTION (first 5 actives) ===")
    turbo = init.get("turbo", {})
    turbo_actives = turbo.get("actives", {})
    print(f"  turbo actives count: {len(turbo_actives)}")
    for aid, data in list(turbo_actives.items())[:5]:
        name = data.get("name", "?")
        enabled = data.get("enabled", False)
        suspended = data.get("is_suspended", True)
        exps = data.get("option", {}).get("expiration_times", [])
        print(f"    {aid}: name={name}, enabled={enabled}, suspended={suspended}, exps={exps[:3]}")

    # Save full init data for analysis
    with open('scratch/init_data_full.json', 'w') as f:
        json.dump(init, f, indent=2)
    print("\nSaved full init data to scratch/init_data_full.json")
else:
    print("init_v2 is None!")

# Also check the v1 result
init_v1 = api.api.api_option_init_all_result
if init_v1:
    print("\n=== V1 INIT DATA KEYS ===")
    if isinstance(init_v1, dict):
        for k in init_v1.keys():
            v = init_v1[k]
            if isinstance(v, dict) and "actives" in v:
                print(f"  {k}: {len(v['actives'])} actives")
            elif isinstance(v, dict):
                print(f"  {k}: dict keys={list(v.keys())[:5]}")
            elif isinstance(v, list):
                print(f"  {k}: list len={len(v)}")
            else:
                print(f"  {k}: {type(v).__name__}")

api.close()
