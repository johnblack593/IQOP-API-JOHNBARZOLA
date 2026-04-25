import os
import json
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.ws.client import WebsocketClient
from iqoptionapi.constants import ACTIVES

# Cargar credenciales
load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

if not email or not password:
    print("Error: IQ_EMAIL o IQ_PASSWORD no encontrados en .env")
    exit(1)

# NUEVA CAPACIDAD 2 — Volcado de TODOS los mensajes por nombre
raw_messages_by_name = {}

# HOOK WebsocketClient.on_message GLOBALLY before connect
original_on_message = WebsocketClient.on_message

def capturing_on_message(self, wss, message):
    try:
        parsed = json.loads(message)
        name = parsed.get("name", "UNNAMED")
        
        if name not in raw_messages_by_name:
            raw_messages_by_name[name] = []
        raw_messages_by_name[name].append(parsed)
    except:
        pass
    return original_on_message(self, wss, message)

WebsocketClient.on_message = capturing_on_message

print(f"Connecting with email: {email}")
api = IQ_Option(email, password)
check, reason = api.connect()
if not check:
    print(f"Failed to connect: {reason}")
    exit(1)

print("Connected successfully. Changing balance to PRACTICE...")
try:
    api.change_balance("PRACTICE")
except Exception as e:
    print(f"Warning: change_balance failed: {e}")

# NUEVA CAPACIDAD 3 — Sniff activo de Digital mediante subscripción
print("\nExecuting ACTIVE SNIFFING (Manual Subscriptions)...")

# Método 1: get-initialization-data v4.0 (bypass normal initialization)
print("  -> Requesting get-initialization-data v4.0")
api.api.websocket.send(json.dumps({
    "name": "get-initialization-data",
    "msg": {"version": "4.0"}
}))
time.sleep(5)

# Método 2: Pedir catálogo digital por segmento
print("  -> Requesting get-instruments (digital-option/digital)")
api.api.websocket.send(json.dumps({
    "name": "get-instruments",
    "msg": {"type": "digital-option", "segment": "digital"}
}))
time.sleep(5)

# Método 3: Pedir underlying-list para digital
print("  -> Requesting get-underlying-list (digital-option)")
api.api.websocket.send(json.dumps({
    "name": "get-underlying-list",
    "msg": {"type": "digital-option"}
}))
time.sleep(5)

# Método 4: Subscripción al stream de digital
print("  -> Subscribing to digital-options-initialization")
api.api.websocket.send(json.dumps({
    "name": "subscribe",
    "msg": {"name": "digital-options-initialization"}
}))

# NUEVA CAPACIDAD 1 — Captura extendida de 60 segundos
print("\nCapturing ALL WS messages for 60 seconds (extended burst)...")
time.sleep(60)

# Guardar volcado por nombre
print("\nDumping messages to JSON files in 'examples/'...")
for name, payloads in raw_messages_by_name.items():
    filename = f"examples/debug_msg_{name}.json"
    with open(filename, "w") as f:
        json.dump(payloads, f, indent=2)
    print(f"  -> Saved {len(payloads)} messages to {filename}")

# NUEVA CAPACIDAD 4 — Extractor de mapeo ACTIVES completo
print("\n=== ACTIVES KYC MAPPING ===")
print(f"Total IDs en ACTIVES: {len(ACTIVES)}")
kyc_targets = [
    "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC",
    "XAUUSD-OTC", "BTCUSD-OTC", "ETHUSD-OTC",
    "EURUSD", "GBPUSD", "USDJPY", "XAUUSD",
    "AAPL", "MSFT", "TSLA", "NVDA", "GOOGL",
    "AMZN", "META", "NFLX", "CISCO", "INTC"
]
for name in kyc_targets:
    active_id = ACTIVES.get(name, "NO ENCONTRADO")
    print(f"  {name}: {active_id}")

with open("examples/debug_actives_kyc_map.json", "w") as f:
    json.dump(dict(ACTIVES), f, indent=2, sort_keys=True)
print("Saved full ACTIVES map to examples/debug_actives_kyc_map.json")

api.close()
print("\nDone.")
