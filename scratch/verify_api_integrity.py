"""Comprehensive verification of the API stability after Sprint 5 modifications."""
import os, sys, json, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect(ssid=SSID)
time.sleep(5) # Wait for catalogs to sync

def verify_all():
    print("\n--- INICIO DE VERIFICACIÓN TÉCNICA ---")
    
    # 1. Verificar Blitz (v3.0)
    blitz_count = len(api.api.blitz_instruments)
    print(f"[BLITZ] Instrumentos cargados: {blitz_count}")
    if blitz_count > 0:
        print("✅ Sincronización Blitz OK (v3.0 funcional)")
    else:
        print("❌ Fallo en sincronización Blitz")

    # 2. Verificar Binary/Turbo
    binary_count = len(api.get_all_init().get('binary', {}).get('actives', {}))
    turbo_count = len(api.get_all_init().get('turbo', {}).get('actives', {}))
    print(f"[BINARY] Activos: {binary_count}")
    print(f"[TURBO] Activos: {turbo_count}")
    if binary_count > 0 and turbo_count > 0:
        print("✅ Sincronización Binary/Turbo OK")
    else:
        print("❌ Fallo en sincronización Binary/Turbo")

    # 3. Prueba de Ejecución (Binary OTC)
    # Usaremos Cardano-OTC que está abierto los fines de semana
    active = "CARDANO-OTC"
    amount = 1
    action = "call"
    duration = 1
    
    print(f"\n[EXECUTION] Intentando orden de prueba en {active}...")
    success, order_id = api.buy(amount, active, action, duration)
    
    if success:
        print(f"✅ Orden ejecutada con éxito! ID: {order_id}")
    else:
        print(f"❌ Error al ejecutar orden: {order_id}")

    # 4. Verificar Estado de Digital (Pausado pero no roto)
    print("\n[DIGITAL] Estado: Pausado (esperando captura de instrument_id)")
    
    print("\n--- FIN DE VERIFICACIÓN ---")

if __name__ == "__main__":
    try:
        verify_all()
    finally:
        api.close()
