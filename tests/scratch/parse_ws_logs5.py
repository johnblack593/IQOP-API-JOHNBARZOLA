import json

filepath = r"C:\Users\JCBV\.gemini\antigravity\brain\5951dd78-873b-4728-823a-fa0ee63e5678\.system_generated\steps\180\output.txt"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if content.startswith("Script ran on page and returned:\n```json\n"):
    content = content.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    
data = json.loads(content)
if isinstance(data, str):
    data = json.loads(data)

print("\n--- FINDING LARGE DOWN MESSAGES ---")
for d in data:
    if d['dir'] == 'DOWN':
        msg = d.get('data', {})
        if isinstance(msg, dict):
            s = json.dumps(msg)
            if len(s) > 10000: # large messages might be the asset catalogs
                print(f"Name: {msg.get('name')}, Size: {len(s)}")
                if msg.get('name') == 'initialization-data':
                    print("  Keys:", list(msg.get('msg', {}).keys()))
                else:
                    print("  Keys:", list(msg.get('msg', {}).keys()) if isinstance(msg.get('msg'), dict) else "N/A")

print("\n--- CHECKING ALL GET-INSTRUMENTS IN DOWN ---")
for d in data:
    if d['dir'] == 'DOWN':
        msg = d.get('data', {})
        if isinstance(msg, dict):
            name = msg.get('name')
            if 'instrument' in str(name).lower() and name != 'initialization-data':
                body = msg.get('msg', {})
                if isinstance(body, dict):
                    print(f"{name}: {list(body.keys())}")
                    if 'instruments' in body:
                        print(f"  Count: {len(body['instruments'])}")
                    elif 'type' in body:
                        print(f"  Type: {body['type']}")
