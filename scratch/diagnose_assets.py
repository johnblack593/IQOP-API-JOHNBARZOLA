import os, json, time
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv
load_dotenv()

iq = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
check, reason = iq.connect()
print(f"Conexion: {check} | {reason}")
iq.change_balance("PRACTICE")

# Test 1: get_all_open_time directo
result = iq.get_all_open_time()
print(f"\nget_all_open_time() tipo: {type(result)}")
print(f"  Claves raiz: {list(result.keys()) if isinstance(result, dict) else 'NO ES DICT'}")
if isinstance(result, dict):
    for cat, items in result.items():
        if isinstance(items, dict):
            open_count = sum(1 for v in items.values() if isinstance(v, dict) and v.get("open"))
            print(f"  [{cat}]: {len(items)} activos, {open_count} abiertos")

# Test 2: ¿Que hay en api.all_open_time crudo?
raw = getattr(iq.api, "all_open_time", None)
print(f"\napi.all_open_time tipo: {type(raw)}")
if isinstance(raw, dict):
    for cat, items in raw.items():
        if isinstance(items, dict):
            open_count = sum(1 for v in items.values() if isinstance(v, dict) and v.get("open"))
            print(f"  [{cat}]: {len(items)} activos, {open_count} abiertos")

# Test 3: ¿get_all_init_v2 tiene activos?
init_data = iq.get_all_init_v2()
print(f"\nget_all_init_v2() tipo: {type(init_data)}")
if init_data and isinstance(init_data, dict):
    for cat in ["binary", "turbo", "digital"]:
        cat_data = init_data.get(cat, {})
        actives = cat_data.get("actives", {}) if isinstance(cat_data, dict) else {}
        print(f"  [{cat}] activos count: {len(actives)}")
        # Buscar primero con is_enabled
        enabled = [k for k, v in actives.items() if isinstance(v, dict) and (v.get("is_enabled") or v.get("enabled"))]
        print(f"  [{cat}] enabled count: {len(enabled)}")

# Test 4: get_instruments por tipo
for itype in ["turbo-option", "digital-option", "binary-option"]:
    insts = iq.get_instruments(itype)
    if insts:
        instruments = insts.get("instruments", [])
        print(f"\nget_instruments({itype!r}): {len(instruments)} instrumentos")
        if len(instruments) > 0:
            first = instruments[0]
            print(f"  Primero keys: {list(first.keys())[:8]}")
            print(f"  Primero sample: name={first.get('name')}, is_enabled={first.get('is_enabled')}, open={first.get('open')}")
    else:
        print(f"\nget_instruments({itype!r}): None/vacio")

iq.api.close()
