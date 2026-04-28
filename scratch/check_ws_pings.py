import json

filepath = r"C:\Users\JCBV\.gemini\antigravity\brain\5951dd78-873b-4728-823a-fa0ee63e5678\.system_generated\steps\180\output.txt"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if content.startswith("Script ran on page and returned:\n```json\n"):
    content = content.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    
data = json.loads(content)
if isinstance(data, str):
    data = json.loads(data)

pings = []
ssids = []
auths = []
gets = []

for d in data:
    msg = d.get('data', {})
    if isinstance(msg, dict):
        if msg.get('resource') == 'ping' or msg.get('name') == 'ping' or msg.get('name') == 'heartbeat':
            pings.append(d)
        if msg.get('name') == 'authenticate':
            auths.append(d)
        if msg.get('name') == 'sendMessage' and 'get-underlying-list' in str(msg):
            gets.append(d)
            
print(f"Total pings found: {len(pings)}")
for p in pings:
    print(p)

print("\nAuths:")
for a in auths:
    print(a)

print("\nGets:")
for g in gets:
    print(g)
