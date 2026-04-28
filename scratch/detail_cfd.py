import json

def detail_cfd():
    with open('open_time.json', 'r') as f:
        data = json.load(f)
    
    cfd = data.get("cfd", {})
    open_cfd = [k for k, v in cfd.items() if v.get("open")]
    print(f"--- OPEN CFD ASSETS ({len(open_cfd)}) ---")
    for asset in sorted(open_cfd):
        print(f"  - {asset}")

    print("\n--- CLOSED CFD ASSETS ---")
    closed_cfd = [k for k, v in cfd.items() if not v.get("open")]
    for asset in sorted(closed_cfd):
        print(f"  - {asset}")

if __name__ == "__main__":
    detail_cfd()
