import json

filepath = r"C:\Users\JCBV\.gemini\antigravity\brain\5951dd78-873b-4728-823a-fa0ee63e5678\.system_generated\steps\180\output.txt"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if content.startswith("Script ran on page and returned:\n```json\n"):
    content = content.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    
data = json.loads(content)
if isinstance(data, str):
    data = json.loads(data)

up_names = set()
for d in data:
    if d['dir'] == 'UP':
        msg = d.get('data', {})
        if isinstance(msg, dict):
            name = msg.get('name')
            if name == 'sendMessage':
                inner_name = msg.get('msg', {}).get('name')
                up_names.add(f"sendMessage -> {inner_name}")
            else:
                up_names.add(str(name))

print("ALL UP MESSAGE NAMES:", sorted(list(up_names)))

print("\n--- FINDING MARGIN REQUESTS ---")
for d in data:
    if d['dir'] == 'UP':
        msg = d.get('data', {})
        if isinstance(msg, dict):
            s = json.dumps(msg).lower()
            if 'instrument' in s or 'margin' in s or 'forex' in s or 'cfd' in s:
                print(f"FOUND: {json.dumps(msg, indent=2)}")

