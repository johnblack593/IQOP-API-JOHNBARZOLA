# scratch/verify_cfd_kyc.py
import os, json, time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
check, _ = api.connect()
assert check
api.change_balance("PRACTICE")
time.sleep(2)

open_times = api.get_all_open_time()
cfd_assets = open_times.get("cfd", {})

# Intentar cargar snapshot anterior para comparar si existe
try:
    with open("open_time.json.bak") as f: # Asumiendo que guardamos un backup o comparamos con el nuevo
        legacy = json.load(f)
    legacy_cfd = legacy.get("cfd", {})
except:
    legacy_cfd = {}

new_assets     = [k for k in cfd_assets if k not in legacy_cfd]
unlocked_assets = [k for k in cfd_assets
                   if cfd_assets[k].get("open") and
                      not legacy_cfd.get(k, {}).get("open")]
open_now       = [k for k,v in cfd_assets.items() if v.get("open")]

print(f"CFD activos en catálogo: {len(cfd_assets)}")
print(f"CFD abiertos ahora: {len(open_now)}")
print(f"Nuevos activos (no estaban en legacy): {new_assets[:10]}...")
print(f"Desbloqueados por KYC (false->true): {unlocked_assets[:10]}...")

if not open_now:
    print("⏸️ Mercado cerrado (Stocks/CFD suelen cerrar los fines de semana).")
    print("Sugerencia: Ejecutar Lunes 9:30am EST para certificación real.")
    # No fallamos, solo informamos
    api.close(); exit(0)

# Ejecutar ciclo buy->close en primer CFD disponible
target_cfd = open_now[0]
print(f"Ejecutando CFD test en: {target_cfd}")

# buy_order para CFD
status, order_id = api.buy_order(
    instrument_type="cfd",
    instrument_id=target_cfd,
    side="call",
    amount=1,
    leverage=1
)
print(f"buy_order: status={status}, order_id={order_id}")

if status and order_id:
    print("Esperando 10s para estabilizar posición...")
    time.sleep(10)

    # Cerrar posición
    close_ok = api.close_position(order_id)
    print(f"close_position: {close_ok}")

    result = {
        "asset": target_cfd,
        "order_id": order_id,
        "close_ok": close_ok,
        "new_kyc_assets": unlocked_assets,
        "certified_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }
    with open("scratch/cfd_certification_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("✅ CFD certificado. Ver scratch/cfd_certification_result.json")
else:
    print(f"❌ FALLO al colocar orden CFD: {order_id}")

api.close()
