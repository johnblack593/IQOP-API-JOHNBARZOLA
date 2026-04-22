
"""
examples/debug_reconnect.py
─────────────────────────────
Valida que la auto-reconexión funciona correctamente.
Simula desconexión forzando api.api.close() y verifica que
el bot se reconecta solo en PRACTICE account.

ADVERTENCIA: ejecutar SOLO en PRACTICE account.
Nunca en cuenta REAL.
"""
import os, time, logging
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
status, reason = api.connect()
if not status:
    print(f"[ERR] connect() fallo: {reason}")
    exit(1)

api.change_balance("PRACTICE")

print("[OK] Conectado. Balance:", api.get_balance())
print("[PWR] Forzando desconexión WS en 2 segundos...")
time.sleep(2)

# Forzar desconexión a nivel WS (simula caída de red)
# Accedemos a la capa baja para cerrar el websocket directamente
api.api.websocket.close()
print("[OUT] WS cerrado. Esperando auto-reconexión (max 60s)...")

# Esperar a que el watchdog o auto-reconnect restauren la conexión
reconnected = False
for i in range(60):
    time.sleep(1)
    if api.check_connect():
        print(f"[OK] Reconectado en {i+1}s. Balance: {api.get_balance()}")
        reconnected = True
        break
    print(f"  [WAIT] {i+1}s — esperando...")

if not reconnected:
    print("[ERR] FALLO: No se reconectó en 60s")

api.close()
