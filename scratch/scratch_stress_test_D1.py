import os, time, sys
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
print("Conectando para Stress Test...")
ok, msg = api.connect()
if not ok:
    print('Error de conexion:', msg)
    sys.exit(1)

print('Conexion exitosa. Cambiando a PRACTICE y configurando balance...')
api.change_balance('PRACTICE')
time.sleep(2)

# Verify Practice mode
if api.get_balance_mode() != 'PRACTICE':
    print('FAIL: No se pudo cambiar a modo PRACTICE')
    sys.exit(1)

# Usaremos un activo Turbo abierto
opened = api.get_all_open_time()
turbo_opened = [k for k, v in opened.get('turbo', {}).items() if v.get('open')]
if not turbo_opened:
    print('FAIL: No hay activos Turbo abiertos para probar.')
    sys.exit(1)

ACTIVO = turbo_opened[0]
MONTO = 1.0
CANTIDAD_TRADES = 10
print(f"Iniciando Stress Test D1: {CANTIDAD_TRADES} trades de {MONTO}$ en {ACTIVO}")

# Execute trades
ids = []
for i in range(CANTIDAD_TRADES):
    # Alternar put/call
    direccion = "call" if i % 2 == 0 else "put"
    print(f"Ejecutando Trade #{i+1}: {direccion} {MONTO}$ en {ACTIVO}...")
    status, id_or_msg = api.buy(MONTO, ACTIVO, direccion, 1) # turbo (1 minuto)
    if status:
        print(f" -> Exito. ID: {id_or_msg}")
        ids.append(id_or_msg)
    else:
        print(f" -> Fallo al comprar: {id_or_msg}")
    time.sleep(1)

if not ids:
    print('FAIL: Ningun trade se pudo ejecutar.')
    sys.exit(1)

print(f"Esperando resultados de {len(ids)} trades...")
for trade_id in ids:
    res, dict_res = api.check_win_v3(trade_id)
    if res:
        print(f"Resultado Trade {trade_id}: Ganancia/Perdida = {dict_res}")
    else:
        print(f"Resultado Trade {trade_id}: Timeout / Fallo en chequeo")

print("Stress Test D1 Completado Exitosamente.")
api.close()
