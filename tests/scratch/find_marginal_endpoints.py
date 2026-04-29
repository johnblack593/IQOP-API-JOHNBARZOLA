import json
import re

filepath = r"C:\Users\JCBV\.gemini\antigravity\brain\5951dd78-873b-4728-823a-fa0ee63e5678\.system_generated\steps\180\output.txt"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if content.startswith("Script ran on page and returned:\n```json\n"):
    content = content.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    
data = json.loads(content)
if isinstance(data, str):
    data = json.loads(data)

marginal_endpoints = set()

for d in data:
    if d['dir'] == 'UP':
        msg = d.get('data', {})
        if isinstance(msg, dict):
            s = json.dumps(msg)
            # Find all strings starting with marginal-
            matches = re.findall(r'"(marginal-[^"]+)"', s)
            for m in matches:
                marginal_endpoints.add(m)
                
print("Found marginal endpoints/names:")
for ep in sorted(list(marginal_endpoints)):
    print(ep)
