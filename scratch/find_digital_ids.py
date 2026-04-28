import json

def find_digital_ids():
    try:
        with open('debug_init.json') as f:
            data = json.load(f)
    except:
        print("Could not load debug_init.json")
        return

    ids = []
    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                if isinstance(v, str) and v.startswith('do') and 'SPT' in v:
                    ids.append(v)
                else:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    print(f"Found {len(ids)} digital IDs")
    for i in ids[:20]:
        print(i)

if __name__ == "__main__":
    find_digital_ids()
