"""Verify asset open status for KYC account."""
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

def verify_assets():
    print("\n--- VERIFICACIÓN DE ESTADO DE ACTIVOS ---")
    
    # Check Binary
    assets = ["EURUSD-OTC", "GBPJPY-OTC", "CARDANO-OTC"]
    for asset in assets:
        is_open = api.check_asset_open(asset)
        # check_asset_open returns (binary_open, turbo_open, digital_open)
        # Actually it's name is a bit ambiguous in different versions.
        # Let's check stable_api.py for its signature.
        print(f"[{asset}] Status: {is_open}")

    # Check Blitz
    print("\n[BLITZ] Checking status...")
    if hasattr(api.api, 'blitz_instruments'):
        for name, data in list(api.api.blitz_instruments.items())[:5]:
            print(f"  {name}: {'OPEN' if data['open'] else 'CLOSED'}")

    print("\n--- FIN DE VERIFICACIÓN ---")

if __name__ == "__main__":
    try:
        verify_assets()
    finally:
        api.close()
