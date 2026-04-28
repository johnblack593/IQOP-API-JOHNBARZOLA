import json

filepath = r"C:\Users\JCBV\.gemini\antigravity\brain\5951dd78-873b-4728-823a-fa0ee63e5678\.system_generated\steps\180\output.txt"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if content.startswith("Script ran on page and returned:\n```json\n"):
    content = content.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    
data = json.loads(content)
if isinstance(data, str):
    data = json.loads(data)

print("\n--- FINDING actives-index ---")
for d in data:
    if d['dir'] == 'DOWN':
        msg = d.get('data', {})
        if isinstance(msg, dict) and msg.get('name') == 'actives-index':
            print("actives-index keys:", list(msg.get('msg', {}).keys()))
            for k, v in msg.get('msg', {}).items():
                print(f"  {k} count: {len(v)}")
            forex = msg.get('msg', {}).get('forex', {})
            if isinstance(forex, dict):
                print("  First forex keys:", list(forex.keys())[:5])
                print("  Sample:", list(forex.values())[:1])
            break

print("\n--- FINDING underlying-list ---")
for d in data:
    if d['dir'] == 'DOWN':
        msg = d.get('data', {})
        if isinstance(msg, dict) and msg.get('name') == 'underlying-list':
            items = msg.get('msg', {}).get('items', [])
            if items:
                print(f"\nunderlying-list items count: {len(items)}")
                print(f"First item keys: {list(items[0].keys())}")
                print(f"First item sample: {json.dumps(items[0])[:200]}")
                types = {}
                for it in items:
                    t = it.get('instrument_type', 'unknown')
                    types[t] = types.get(t, 0) + 1
                print(f"Types in underlying-list: {types}")

print("\n--- FINDING underlying-list-changed ---")
for d in data:
    if d['dir'] == 'DOWN':
        msg = d.get('data', {})
        if isinstance(msg, dict) and msg.get('name') == 'underlying-list-changed':
            underlying = msg.get('msg', {}).get('underlying', [])
            print(f"\nunderlying-list-changed count: {len(underlying)}")
            if underlying:
                types = {}
                for it in underlying:
                    t = it.get('instrument_type', 'unknown')
                    types[t] = types.get(t, 0) + 1
                print(f"Types in underlying-list-changed: {types}")
            break
