import os
import json
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

print("=== VERIFICACION INTEGRACION DIGITAL (Sprint 6 FINAL) ===")
api = IQ_Option(email, password)
check, reason = api.connect()
if not check:
    print(f"Failed to connect: {reason}")
    exit(1)

api.change_balance("PRACTICE")

# Activo: EURUSD-OTC (ID 76)
asset = "EURUSD-OTC"

print(f"Ejecutando buy_digital_spot_v2('{asset}', 1, 'call', 1)...")
# Esto ahora deberia generar el ID 'do76A...' internamente
check, order_id = api.buy_digital_spot_v2(asset, 1, "call", 1)

if check:
    print(f"ORDEN EXITOSA: {order_id}")
    time.sleep(2)
    positions = api.get_positions("digital-option")
    print(f"Posiciones abiertas: {len(positions)}")
else:
    print(f"FALLO: {order_id}")

api.close()
