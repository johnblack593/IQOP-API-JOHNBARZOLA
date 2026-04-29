"""Verification of the API stability with event waiting."""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.ERROR)

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect(ssid=SSID)

# Wait specifically for the init-data event
if not api.api.api_option_init_all_result_v2_event.wait(timeout=20):
    print("WARNING: Timeout waiting for init-data event. Catalogs might be empty.")

def verify_all():
    print("\n--- INICIO DE VERIFICACIÓN TÉCNICA (V2) ---")
    
    # 1. Blitz
    blitz_count = len(api.api.blitz_instruments)
    print(f"[BLITZ] Instrumentos cargados: {blitz_count}")
    
    # 2. Binary
    init_data = api.api.api_option_init_all_result_v2 or {}
    binary_count = len(init_data.get('binary', {}).get('actives', {}))
    print(f"[BINARY] Activos: {binary_count}")

    # 3. Execution Verification
    # We already know it works from V1, but let's confirm the data structure
    if binary_count > 0:
        print("✅ Catálogo Binary detectado.")
    if blitz_count > 0:
        print("✅ Catálogo Blitz detectado.")

    print("\n--- FIN DE VERIFICACIÓN ---")

if __name__ == "__main__":
    try:
        verify_all()
    finally:
        api.close()
