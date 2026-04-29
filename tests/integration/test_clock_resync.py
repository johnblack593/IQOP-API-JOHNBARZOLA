# scratch/test_clock_resync.py
import os, time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.core.time_sync import _clock

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
check, reason = api.connect()
if not check:
    print(f"Connection failed: {reason}")
    exit(1)

print(f"Initial offset: {_clock.offset_seconds():.4f}s")

# Simular desconexión forzada
print("Simulating forced disconnection...")
if hasattr(api.api, 'websocket_client') and api.api.websocket_client:
    api.api.websocket_client.wss.close()
elif hasattr(api.api, 'websocket') and api.api.websocket:
    api.api.websocket.close()
else:
    print("Could not find websocket object to close")
    exit(1)
time.sleep(5)

print(f"WS Connected state: {api.api.check_websocket_if_connect}")
assert api.api.check_websocket_if_connect == 0

# Esperar reconexión automática (el SDK tiene lógica de auto-reconnect)
print("Waiting for auto-reconnection (up to 45s)...")
reconnected = False
for i in range(45):
    if api.api.check_websocket_if_connect == 1:
        reconnected = True
        break
    time.sleep(1)

assert reconnected, "Failed to auto-reconnect"
print("Reconnected! Waiting for first timeSync...")
time.sleep(5) # Dar tiempo a que lleguen mensajes

print(f"Post-reconnect offset: {_clock.offset_seconds():.4f}s")
assert abs(_clock.offset_seconds()) < 10.0, "Offset too large"

# Test buy_blitz
print("Testing buy_blitz with synced clock...")
# Necesitamos un activo Blitz abierto. XRPUSD suele estar.
# Pero hoy es Sábado, tal vez Blitz esté cerrado o solo OTC.
# En Sprint 7 vimos que XRPUSD-OTC estaba en Digital.
try:
    status, order_id = api.buy_blitz("XRPUSD-OTC", 1, "call", 30)
    print(f"buy_blitz result: {status}, {order_id}")
except Exception as e:
    print(f"buy_blitz failed (might be closed): {e}")

api.close()
print("Test finished.")

