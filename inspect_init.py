import json

with open("full_init.json", "r") as f:
    data = json.load(f)

print("Keys in initialization-data:")
print(data.keys())

for k in data.keys():
    if isinstance(data[k], dict):
        print(f"Sub-keys in {k}:")
        print(list(data[k].keys())[:10])
