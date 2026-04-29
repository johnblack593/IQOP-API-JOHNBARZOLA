"""Verify Blitz order execution."""
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

def test_blitz():
    print("\n--- PRUEBA DE EJECUCIÓN BLITZ ---")
    
    # Use an active from blitz_instruments
    # Usually EURUSD-OTC or similar
    active = "EURUSD-OTC"
    amount = 1
    action = "call"
    duration = 30 # Blitz uses seconds
    
    print(f"Intentando orden Blitz en {active} ({duration}s)...")
    success, order_id = api.buy_blitz(active, amount, action, duration)
    
    if success:
        print(f"✅ Orden Blitz exitosa! ID: {order_id}")
    else:
        print(f"❌ Fallo en orden Blitz: {order_id}")

    print("\n--- FIN DE PRUEBA ---")

if __name__ == "__main__":
    try:
        test_blitz()
    finally:
        api.close()
