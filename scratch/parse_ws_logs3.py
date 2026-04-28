import json

filepath = r"C:\Users\JCBV\.gemini\antigravity\brain\5951dd78-873b-4728-823a-fa0ee63e5678\.system_generated\steps\180\output.txt"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if content.startswith("Script ran on page and returned:\n```json\n"):
    content = content.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    
data = json.loads(content)
if isinstance(data, str):
    data = json.loads(data)

print("ALL UP MESSAGES AFTER AUTH:")
for i, d in enumerate(data):
    if d['dir'] == 'UP':
        msg = d.get('data', {})
        if isinstance(msg, dict):
            name = msg.get('name')
            if name == 'sendMessage':
                inner_name = msg.get('msg', {}).get('name')
                print(f"{i:04d} | sendMessage -> {inner_name}")
            elif name == 'subscribeMessage':
                inner_name = msg.get('msg', {}).get('name')
                print(f"{i:04d} | subscribeMessage -> {inner_name}")
            elif name == 'authenticate':
                print(f"{i:04d} | authenticate")
            else:
                print(f"{i:04d} | {name}")
