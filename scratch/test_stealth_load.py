import time
import logging
import sys
import os

# Añadir el path del SDK
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def test_stealth_load():
    email = os.getenv("IQ_EMAIL", "tu_email@gmail.com")
    password = os.getenv("IQ_PASS", "tu_password")
    
    I_api = IQ_Option(email, password)
    I_api.connect()
    
    # Lista de activos para saturar suscripciones
    actives = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURGBP", "EURJPY"]
    
    print(f"\n--- Probando Carga Stealth (Batch Subscribe) ---")
    print(f"Suscribiendo a {len(actives)} activos simultáneamente...")
    
    for active in actives:
        # Esto debería encolarse en el SubscriptionManager
        I_api.start_candles_stream(active, 60, 10)
        
    print("Suscripciones encoladas. Esperando procesamiento del Dispatcher...")
    
    # Deberíamos ver logs del SubManager con delays entre cada suscripción
    time.sleep(10)
    
    print("\nSimulando reconexión (trigger re_subscribe_stream)...")
    I_api.re_subscribe_stream()
    
    time.sleep(10)
    
    I_api.api.close()
    print("\n--- Test Finalizado ---")

if __name__ == "__main__":
    test_stealth_load()
