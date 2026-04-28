import json

filepath = r"C:\Users\JCBV\.gemini\antigravity\brain\5951dd78-873b-4728-823a-fa0ee63e5678\.system_generated\steps\180\output.txt"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if content.startswith("Script ran on page and returned:\n```json\n"):
    content = content.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    
data = json.loads(content)
if isinstance(data, str):
    data = json.loads(data)

print("\n--- FINDING instruments-list ITEMS COUNT ---")
for d in data:
    if d['dir'] == 'DOWN':
        msg = d.get('data', {})
        if isinstance(msg, dict):
            name = msg.get('name')
            if name == 'instruments-list':
                items = msg.get('msg', {}).get('items', [])
                print(f"instruments-list count: {len(items)}")
                if items:
                    print(f"First item keys: {list(items[0].keys())}")
                    # Print one sample
                    print("Sample:", json.dumps(items[0])[:500])
                    break
