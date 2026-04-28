import os, json, time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
check, _ = api.connect()
if not check:
    print("Failed to connect")
    exit(1)

api.change_balance("PRACTICE")
time.sleep(2)

print("Solicitando catálogo completo (esto puede tardar 2-3 minutos)...")
full_catalog = api.get_all_open_time()

# Guardar
with open("open_time.json", "w") as f:
    json.dump(full_catalog, f, indent=2, sort_keys=True)

print(f"✅ open_time.json regenerado. Activos por categoría:")
for cat in full_catalog:
    print(f"  {cat}: {len(full_catalog[cat])}")

api.close()
