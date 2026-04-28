import json

filepath = r"C:\Users\JCBV\.gemini\antigravity\brain\5951dd78-873b-4728-823a-fa0ee63e5678\.system_generated\steps\180\output.txt"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if content.startswith("Script ran on page and returned:\n```json\n"):
    content = content.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    
data = json.loads(content)
if isinstance(data, str):
    data = json.loads(data)

print("\n--- FINDING get-instruments-list ---")
for d in data:
    if d['dir'] == 'UP':
        msg = d.get('data', {})
        if isinstance(msg, dict):
            name = msg.get('name')
            if name == 'sendMessage':
                inner_name = msg.get('msg', {}).get('name', '')
                if 'get-instruments-list' in str(inner_name):
                    print(json.dumps(msg, indent=2))

print("\n--- FINDING get-instruments-list RESPONSES ---")
for d in data:
    if d['dir'] == 'DOWN':
        msg = d.get('data', {})
        if isinstance(msg, dict):
            name = msg.get('name')
            if 'instruments' in str(name).lower() or 'get' in str(name).lower() or isinstance(msg.get('msg'), dict) and 'instruments' in str(msg.get('msg')):
                if msg.get('request_id') in ['177', '178', '179', '180']: # Example IDs, let's just print names
                    pass
                if 'get-instruments-list' in str(name):
                    print(f"Name: {name}, Keys: {list(msg.get('msg', {}).keys())}")
                    instruments = msg.get('msg', {}).get('instruments', [])
                    print(f"Count: {len(instruments)}")
                    if instruments:
                        print(f"First: {instruments[0].keys()}")
