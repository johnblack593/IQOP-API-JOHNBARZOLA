import os, json, time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
api.connect()
api.change_balance("PRACTICE")

open_times = api.get_all_open_time()

# DIAGNÓSTICO 1: ¿Hay activos CFD/Forex en open_time?
for cat in ["cfd", "forex"]:
    cat_data = open_times.get(cat, {})
    open_assets = {k: v for k, v in cat_data.items() if v.get("open") is True}
    print(f"\n{cat.upper()} in open_time: {len(cat_data)} total, {len(open_assets)} open")
    print(f"  Open examples: {list(open_assets.keys())[:8]}")
    if cat_data:
        sample = list(cat_data.items())[0]
        print(f"  Sample structure: {sample[0]} -> {sample[1]}")

# DIAGNÓSTICO 2: ¿Hay activos digital en open_time?
digital_data = open_times.get("digital", {})
digital_open = {k: v for k, v in digital_data.items() if v.get("open") is True}
print(f"\nDIGITAL in open_time: {len(digital_data)} total, {len(digital_open)} open")
print(f"  Open examples: {list(digital_open.keys())[:8]}")
if digital_data:
    sample = list(digital_data.items())[0]
    print(f"  Sample structure: {sample[0]} -> {sample[1]}")

# DIAGNÓSTICO 3: WS messages buscando endpoint digital alternativo
# IQ Option puede tener V3 o usar "digital-option" en lugar de "digital"
print("\n=== Capturando mensajes WS con 'digital' por 10 segundos ===")
captured = []
orig = api.api.websocket_client.on_message
def cap(wss, msg):
    try:
        import json as j
        p = j.loads(msg)
        name = p.get("name","")
        if "digital" in name.lower() or "underlying" in name.lower():
            captured.append({"name": name, "keys": list(p.get("msg",{}).keys()) if isinstance(p.get("msg"),dict) else str(type(p.get("msg")))})
    except: pass
    orig(wss, msg)
api.api.websocket_client.on_message = cap
api.api.get_digital_underlying()  # intentar el request original
time.sleep(10)
print(f"Captured digital-related WS messages: {len(captured)}")
for m in captured[:10]:
    print(f"  {m}")

# DIAGNÓSTICO 4: Intentar get_instruments con tipos alternativos
for itype in ["digital-option", "digital_option", "digital",
                "fx-option", "cfd", "forex"]:
    try:
        result = api.get_instruments(itype)
        count = len(result.get("instruments", []))
        print(f"\nget_instruments('{itype}'): {count} instruments")
        if count > 0:
            print(f"  Sample: {result['instruments'][0].get('name','?')}")
    except Exception as e:
        print(f"\nget_instruments('{itype}'): ERROR {e}")

# Guardar open_times completo para análisis
with open("examples/debug_s12_open_times.json", "w") as f:
    json.dump({k: dict(list(v.items())[:5]) for k,v in open_times.items()}, f, indent=2)

print("\nDump guardado: examples/debug_s12_open_times.json")
api.close()
