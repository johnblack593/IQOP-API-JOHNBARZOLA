import json
import os

filepath = r"C:\Users\JCBV\.gemini\antigravity\brain\5951dd78-873b-4728-823a-fa0ee63e5678\.system_generated\steps\180\output.txt"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if content.startswith("Script ran on page and returned:\n```json\n"):
    content = content.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    
data = json.loads(content)
if isinstance(data, str):
    data = json.loads(data)

print("TOTAL MESSAGES:", len(data))

print("\n--- AUTHENTICATION MESSAGES ---")
for d in data[:50]:
    msg_data = d.get('data')
    if isinstance(msg_data, dict):
        name = msg_data.get('name', '')
        if name == 'ssid':
            print("AUTH FOUND (DOWN):", json.dumps(msg_data, indent=2)[:300])
        elif name == 'authenticate':
            print("AUTH FOUND (UP):", json.dumps(msg_data, indent=2)[:300])

print("\n--- GET-INSTRUMENTS PAYLOADS (UP) ---")
for d in data:
    if d['dir'] == 'UP':
        msg_data = d.get('data')
        if isinstance(msg_data, dict) and msg_data.get('name') == 'sendMessage':
            inner_name = msg_data.get('msg', {}).get('name', '')
            if inner_name == 'get-instruments':
                print(json.dumps(msg_data, indent=2))
        elif isinstance(msg_data, dict) and msg_data.get('name') == 'get-instruments':
            print(json.dumps(msg_data, indent=2))

print("\n--- INSTRUMENTS RESPONSES (DOWN) ---")
for d in data:
    if d['dir'] == 'DOWN':
        msg_data = d.get('data')
        if isinstance(msg_data, dict) and msg_data.get('name') in ['instruments', 'get-instruments']:
            body = msg_data.get('msg', {})
            t = body.get('type')
            instruments = body.get('instruments', [])
            if not instruments and isinstance(body, dict) and 'instruments' not in body:
                print(f"Name: {msg_data.get('name')}, body keys: {list(body.keys())}")
            count = len(instruments)
            print(f"Name: {msg_data.get('name')}, Type: {t}, count: {count}")
            if count > 0:
                print("First instrument keys:", list(instruments[0].keys()))

