import os
import json
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.ws.client import WebsocketClient

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

# HOOK WebsocketClient.on_message GLOBALLY before connect
raw_messages = []
original_on_message = WebsocketClient.on_message

def capturing_on_message(self, wss, message):
    try:
        parsed = json.loads(message)
        name = parsed.get("name", "UNNAMED")
        # Log to list
        raw_messages.append(parsed)
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


# 1. Dump completo de open_time
open_times = api.get_all_open_time()
with open("examples/debug_open_time.json", "w") as f:
    json.dump(open_times, f, indent=2)

# 2. Dump de instruments
categories = ["binary-option", "blitz", "turbo-option", "digital-option", "fx-option"]
for category in categories:
    try:
        result = api.get_instruments(category)
        with open(f"examples/debug_instruments_{category}.json", "w") as f:
            json.dump(result, f, indent=2)
    except:
        pass

# 3. Capture more messages
print("Capturing more WS messages for 10 seconds...")
time.sleep(10)

# --- SECCIÓN 4: Mapeo de threading.Event vs mensajes WS ---
print("\n=== EVENTS MAP ===")
events_in_api = [attr for attr in dir(api.api) if attr.endswith('_event')]
print(f"threading.Event existentes en api.api: {events_in_api}")

# Verificar cuáles ya tienen handlers en _MESSAGE_ROUTER
from iqoptionapi.ws.client import _MESSAGE_ROUTER
print(f"\nMensajes con handler registrado: {sorted(_MESSAGE_ROUTER.keys())}")
print(f"\nMensajes SIN handler (capturados en WS pero no en router):")
unique_captured = set([m.get("name") for m in raw_messages if isinstance(m, dict)])
for name in unique_captured:
    if name and name not in _MESSAGE_ROUTER:
        print(f"  [MISSING HANDLER] {name}")

# --- SECCIÓN 5: Verificar spin-loops candidatos ---
print("\n=== SPIN-LOOP CANDIDATES ===")
# Estos son los métodos con spin-loops identificados.
# Verificar que sus eventos WS siguen activos en el servidor.
candidates = {
    "get_candles":          "candles",
    "get_all_init":         "api_option_init_all_result",
    "get_all_init_v2":      "initialization-data",
    "get_profile":          "profile",
    "get_technical_indicators": "technical-indicators",
    "get_digital_underlying": "underlying-list",
    "reset_practice_balance": "training-balance-reset",
    "get_user_profile_client": "user-profile-client",
    "get_users_availability":  "users-availability",
    "get_order":            "order",
    "get_positions":        "positions",
    "get_position":         "position",
    "get_history_positions":"history-positions",
    "get_position_history": "position-history",
}
for method, ws_name in candidates.items():
    captured = ws_name in unique_captured
    in_router = ws_name in _MESSAGE_ROUTER
    status = "[OK]" if (captured or in_router) else "[NO] NOT FOUND"
    print(f"  {status} {method}() -> WS '{ws_name}'")

api.close()
