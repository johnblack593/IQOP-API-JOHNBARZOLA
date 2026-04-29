"""Debug: Capture raw WS messages after buy_blitz to find the response channel."""
import os, sys, json, time, logging, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')

SSID = "05ac28045097edb0fcde0d87e0ce207q"
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
status, reason = api.connect(ssid=SSID)
if not status:
    print(f"FAIL: {reason}")
    sys.exit(1)

api.change_balance("PRACTICE")
time.sleep(3)

# Monkey-patch the websocket message handler to log ALL messages
original_on_message = api.api.websocket_client.on_message
captured_messages = []

def capture_on_message(message):
    try:
        msg = json.loads(message)
        name = msg.get("name", "?")
        captured_messages.append({
            "time": time.time(),
            "name": name,
            "msg": msg.get("msg", {}),
            "request_id": msg.get("request_id", ""),
        })
    except:
        pass
    return original_on_message(message)

api.api.websocket_client.on_message = capture_on_message

print(f"\n=== TEST: buy_blitz CARDANO-OTC 30s ===")
print(f"Blitz catalog: {len(api.api.blitz_instruments)} instruments")

# Clear captured messages
captured_messages.clear()

# Execute buy_blitz
success, order_id = api.buy_blitz("CARDANO-OTC", 1, "call", 30)
print(f"Result: success={success}, order_id={order_id}")

# Wait a bit for any delayed messages
time.sleep(3)

# Dump ALL captured messages
print(f"\n=== CAPTURED WS MESSAGES ({len(captured_messages)} total) ===")
for i, msg in enumerate(captured_messages):
    name = msg["name"]
    req_id = msg["request_id"]
    # Show full msg for relevant ones
    if name in ["option", "option-closed", "option-changed", "listInfoData",
                 "buyComplete", "result", "binary-options.open-option",
                 "option-opened", "tradersPulse"]:
        print(f"\n  [{i}] name={name} req_id={req_id}")
        print(f"      msg={json.dumps(msg['msg'], indent=6)[:500]}")
    else:
        print(f"  [{i}] name={name} req_id={req_id}")

# Also check buy_multi_option state
print(f"\n=== buy_multi_option state ===")
print(json.dumps(api.api.buy_multi_option, indent=2, default=str))

print(f"\n=== api.result ===")
print(f"result = {api.api.result}")

# Save all captured
with open('scratch/blitz_ws_capture.json', 'w') as f:
    json.dump(captured_messages, f, indent=2, default=str)

api.close()
