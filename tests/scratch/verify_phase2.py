import os
import time
import threading
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

if not email or not password:
    print("🔴 ANOMALIA: IQ_EMAIL o IQ_PASSWORD no definidos")
    exit(1)

print(f"--- FASE 2: VERIFICACION DINAMICA ---")
print(f"Email: {email}")

iq = IQ_Option(email, password)

# Paso 2.1 - Conexion
t_start = time.time()
check, reason = iq.connect()
elapsed = time.time() - t_start

if not check:
    print(f"FAIL ANOMALIA: Conexion fallida en {elapsed:.1f}s")
    print(f"  Razon: {reason}")
    exit(1)

print(f"OK Conexion exitosa en {elapsed:.1f}s")

# Cambiar a cuenta demo
iq.change_balance("PRACTICE")
balance = iq.get_balance()
print(f"OK Balance PRACTICE: ${balance}")

# Paso 2.2 - Perfil y balance_id
profile = iq.get_profile_ansyc()
if profile is None or "balances" not in profile:
    print(f"FAIL ANOMALIA: Perfil invalido o sin balances: {profile}")
    # Intentar obtener balances de otra forma si es necesario
else:
    balance_id = getattr(iq.api, "balance_id", None)
    print(f"OK balance_id: {balance_id}")

# Paso 2.3 - Stream de velas
print("\n--- Test: Candle Stream ---")
t = time.time()
result = iq.start_candles_one_stream("EURUSD", 60)
elapsed_subscribe = time.time() - t
print(f"  start_candles_one_stream retorno en {elapsed_subscribe:.2f}s")

time.sleep(5)
candles = iq.get_realtime_candles("EURUSD", 60)
if candles:
    print(f"OK Stream OK: {len(candles)} velas recibidas")
else:
    print("WARN ADVERTENCIA: 0 velas recibidas")

iq.stop_candles_one_stream("EURUSD", 60)

# Paso 2.4 - Activos disponibles
print("\n--- Test: Activos disponibles ---")
assets = iq.get_all_open_time()
binary_open = [k for k, v in assets.get("turbo", {}).items() if v.get("open")]
digital_open = [k for k, v in assets.get("digital", {}).items() if v.get("open")]
print(f"  Activos Binary/Turbo abiertos: {len(binary_open)}")
print(f"  Activos Digital abiertos: {len(digital_open)}")

test_asset = binary_open[0] if binary_open else None
test_digital_asset = digital_open[0] if digital_open else None

# Paso 2.5 - Test Binary (check_win_v4)
print("\n--- Test: Binary Option (check_win_v4) ---")
if test_asset:
    print(f"  Probando con: {test_asset}")
    check, order_id = iq.buy(1, test_asset, "call", 1)
    if not check:
        print(f"WARN buy() retorno False: {order_id}")
    else:
        print(f"OK Orden Binary colocada: {order_id}")
        t_start = time.time()
        result = iq.check_win_v4(order_id)
        elapsed = time.time() - t_start
        print(f"OK check_win_v4 en {elapsed:.1f}s: {result}")
else:
    print("WARN Saltando: sin activos binarios")

# Paso 2.6 - Test Digital Option
print("\n--- Test: Digital Option ---")
if test_digital_asset:
    print(f"  Probando con: {test_digital_asset}")
    check, order_id = iq.buy_digital_spot(test_digital_asset, 1, "call", 1)
    if not check:
        print(f"WARN buy_digital_spot() retorno False: {order_id}")
    else:
        print(f"OK Orden Digital colocada: {order_id}")
        t_start = time.time()
        result = iq.check_win_digital_v2(order_id)
        elapsed = time.time() - t_start
        print(f"OK check_win_digital_v2 en {elapsed:.1f}s: {result}")
else:
    print("WARN Saltando: sin activos digitales")

# Paso 2.7 - Kill-Switch
print("\n--- Test: Kill-Switch ---")
test_event_fired = threading.Event()
test_result = {}

def dummy_waiter():
    dummy_order_id = 999999999
    evt = iq.api.result_event_store[dummy_order_id]
    triggered = evt.wait(timeout=30)
    test_result["triggered"] = triggered
    test_event_fired.set()

t = threading.Thread(target=dummy_waiter, daemon=True)
t.start()
time.sleep(1)
print("  Cerrando conexion para activar kill-switch...")
iq.api.close()
test_event_fired.wait(timeout=10)
if t.is_alive():
    print("FAIL ANOMALIA: Kill-switch no libero el thread")
else:
    print("OK Kill-switch OK: thread liberado")

print("\n--- FIN DE PRUEBAS ---")
