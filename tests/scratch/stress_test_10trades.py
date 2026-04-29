"""
stress_test_10trades.py -- PRACTICE ONLY
Prueba gradual de 5 trades con pausas humanas entre cada uno.
Disenado para NO activar rate limits ni baneo de IP.

Reglas anti-baneo:
  - Maximo 5 trades por sesion
  - Pausa minima 10s entre trades (simula comportamiento humano)
  - Log diagnostico de IP (informativo, no bloquea)
  - Si WS se desconecta, aborta limpiamente (no reintenta)
  - Monto maximo $1.00

TVC-FIX-20260427-ST10v3
"""
import os, sys, time, logging, random
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s: %(message)s')
load_dotenv()

# ── Paso 0: Diagnostico de IP (solo informativo) ────────────
from iqoptionapi.ip_rotation import log_ip_diagnostic

print("=== Pre-flight: Diagnostico IP ===")
geo = log_ip_diagnostic()
if geo:
    print(f"  IP: {geo['ip']}")
    print(f"  Ubicacion: {geo['city']}, {geo['region']}, {geo['country']}")
    print(f"  Org: {geo['org']}")
    print(f"  (Nota: IQ Option vincula la cuenta al pais de registro,")
    print(f"   no a la IP de conexion. La IP NO bloquea la operacion.)\n")
else:
    print("  No se pudo verificar IP. Continuando.\n")

# ── Paso 1: Conectar ────────────────────────────────────────
from iqoptionapi.stable_api import IQ_Option

MAX_TRADES = 5
PAUSE_MIN = 10   # segundos minimos entre trades
PAUSE_MAX = 15   # segundos maximos (jitter humano)
AMOUNT = 1.0     # maximo $1

api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
ok, msg = api.connect()
if not ok:
    print(f"CONEXION FALLIDA: {msg}")
    sys.exit(1)

api.change_balance("PRACTICE")
time.sleep(3)

# Validar balance_id
if api.api.balance_id is None:
    api.get_profile_ansyc()
    time.sleep(3)
if api.api.balance_id is None:
    print("FATAL: balance_id=None. La conexion no se estabilizo.")
    sys.exit(1)

# ── Paso 2: Obtener activos sin sobrecarga ──────────────────
# Usar init_v2 directo (evita multiples WS requests de get_all_open_time)
init_v2 = api.get_all_init_v2()
turbo_assets = []
if init_v2 and 'turbo' in init_v2:
    for a_id, info in init_v2['turbo'].get('actives', {}).items():
        if info.get('enabled') and not info.get('is_suspended'):
            name = info.get('name', '').replace('front.', '')
            if '-OTC' in name:  # preferir OTC (24/7)
                turbo_assets.append(name)

if not turbo_assets:
    print("FATAL: No hay activos Turbo-OTC disponibles.")
    try: api.close()
    except: pass
    sys.exit(1)

ASSET = next((a for a in ['EURUSD-OTC', 'GBPUSD-OTC', 'AUDCAD-OTC']
              if a in turbo_assets), turbo_assets[0])

try:
    balance_start = api.get_balance()
    print(f"Activo: {ASSET}")
    print(f"Balance inicial: ${balance_start:.2f}")
except:
    print("No se pudo leer balance. WS posiblemente inestable.")
    balance_start = 0

print(f"Ejecutando {MAX_TRADES} trades con pausas de {PAUSE_MIN}-{PAUSE_MAX}s\n")

# ── Paso 3: Ejecutar trades con ritmo humano ────────────────
results = []
for i in range(MAX_TRADES):
    # Verificar WS antes de cada trade
    if not api.check_connect():
        print(f"  Trade {i+1}: WS desconectado. ABORTANDO (no reintentar).")
        results.append({"trade": i+1, "status": "WS_DEAD", "profit": None})
        break

    direction = "call" if i % 2 == 0 else "put"
    print(f"  Trade {i+1}/{MAX_TRADES}: {direction.upper()} ${AMOUNT} en {ASSET}...", end="", flush=True)

    try:
        status, order_id = api.buy(AMOUNT, ASSET, direction, 1)
    except Exception as e:
        print(f" EXCEPCION: {e}")
        results.append({"trade": i+1, "status": "BUY_EXCEPTION", "profit": None})
        break  # No reintentar

    if not status:
        print(f" RECHAZADO: {order_id}")
        results.append({"trade": i+1, "status": "BUY_FAILED", "detail": str(order_id), "profit": None})
        time.sleep(5)
        continue

    print(f" OK (order={order_id})")

    # Esperar resultado — timeout 90s (1m trade + 30s buffer)
    t0 = time.time()
    profit = api.check_win_v3(order_id, 90)
    elapsed = time.time() - t0

    if profit is not None and profit > 0:
        res = "WIN"
    elif profit is not None and profit < 0:
        res = "LOSS"
    elif profit is not None:
        res = "EQUAL"
    else:
        res = "TIMEOUT"

    results.append({"trade": i+1, "order_id": order_id,
                     "status": res, "profit": profit,
                     "elapsed": round(elapsed, 1)})
    print(f"    -> {res} profit={profit} ({elapsed:.1f}s)")

    # Pausa humana entre trades (jitter aleatorio)
    if i < MAX_TRADES - 1:
        pause = random.uniform(PAUSE_MIN, PAUSE_MAX)
        print(f"    Pausa {pause:.0f}s...", flush=True)
        time.sleep(pause)

# ── Paso 4: Reporte ─────────────────────────────────────────
resolved = [r for r in results if r['status'] in ('WIN', 'LOSS', 'EQUAL')]
timeouts = [r for r in results if r['status'] == 'TIMEOUT']
failures = [r for r in results if r['status'] in ('BUY_FAILED', 'BUY_EXCEPTION', 'WS_DEAD')]
wins = [r for r in resolved if r['status'] == 'WIN']
total_profit = sum(r.get('profit', 0) or 0 for r in resolved)

print(f"\n{'='*50}")
print(f"STRESS TEST {MAX_TRADES} TRADES -- RESULTADO FINAL")
print(f"{'='*50}")
print(f"Ejecutados: {len(results)}/{MAX_TRADES}")
print(f"Resueltos:  {len(resolved)}/{MAX_TRADES}")
print(f"Timeouts:   {len(timeouts)}/{MAX_TRADES}")
print(f"Fallos:     {len(failures)}/{MAX_TRADES}")
if resolved:
    print(f"Win rate:   {len(wins)}/{len(resolved)} ({len(wins)/len(resolved)*100:.0f}%)")
    print(f"P&L neto:   ${total_profit:.2f}")

try:
    balance_end = api.get_balance()
    print(f"Balance:    ${balance_start:.2f} -> ${balance_end:.2f} (delta: ${balance_end - balance_start:+.2f})")
except:
    print(f"Balance final: N/A")

if len(resolved) == MAX_TRADES:
    print(f"\nRESULTADO: PASADO ({MAX_TRADES}/{MAX_TRADES} trades resueltos)")
elif len(resolved) >= MAX_TRADES * 0.6:
    print(f"\nRESULTADO: ACEPTABLE ({len(resolved)}/{MAX_TRADES} resueltos)")
else:
    print(f"\nRESULTADO: NECESITA REVISION ({len(resolved)}/{MAX_TRADES} resueltos)")

try: api.close()
except: pass
