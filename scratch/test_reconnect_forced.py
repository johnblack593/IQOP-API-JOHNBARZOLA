"""
test_reconnect_forced.py — verifica que el SDK sobrevive
un corte de WS y se recupera sin intervención manual.
"""
import os, time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()
api.change_balance("PRACTICE")
time.sleep(2)
print("Estado pre-corte:")
print("  Balance:", api.get_balance())

# Forzar cierre del WebSocket
print("Forzando cierre del WebSocket...")
try:
    api.api.websocket.close()
except Exception as e:
    print(f"  (close() lanzó: {e} — normal)")

# Esperar reconexión automática (max 30s)
print("Esperando reconexión automática...")
for i in range(30):
    time.sleep(1)
    try:
        bal = api.get_balance()
        if bal and bal > 0:
            print(f"  Reconectado en {i+1}s | Balance: {bal:.2f}")
            break
    except:
        pass
else:
    print("  FALLO: No reconectó en 30s — ReconnectManager requiere fix")
    # DIAGNOSTICO: verificar si reconnect.py tiene hook en on_close
    # grep: api.api.websocket.on_close o on_error

# Verificar estado post-reconexión
ot = api.get_all_open_time()
turbo = [k for k,v in ot.get('turbo',{}).items() if v.get('open')]
print(f"  Turbo activos post-reconexion: {len(turbo)}")
from iqoptionapi.time_sync import _clock
print(f"  Clock offset post-reconexion: {_clock.offset_seconds():.3f}s")
# Trade de verificación final
if turbo:
    asset = turbo[0]
    ok, oid = api.buy(1.0, asset, 'call', 1)
    print(f"  Trade post-reconexion: status={ok} order={oid}")
