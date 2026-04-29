"""Verify all profit status for KYC account."""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.ERROR)

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect(ssid=SSID)
time.sleep(5)

def verify_profits():
    print("\n--- VERIFICACIÓN DE GANANCIAS (PROFIT) ---")
    
    profits = api.get_all_profit()
    assets = ["EURUSD-OTC", "GBPJPY-OTC", "CARDANO-OTC"]
    
    for asset in assets:
        p = profits.get(asset)
        print(f"[{asset}] Profit: {p}")
        if p:
            print(f"  Turbo: {p.get('turbo')}%")
            print(f"  Binary: {p.get('binary')}%")

    print("\n--- FIN DE VERIFICACIÓN ---")

if __name__ == "__main__":
    try:
        verify_profits()
    finally:
        api.close()
