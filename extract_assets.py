import json

def extract_details():
    with open("full_init.json", "r") as f:
        data = json.load(f)
    
    digital_actives = data.get("digital", {}).get("actives", {})
    turbo_actives = data.get("turbo", {}).get("actives", {})
    
    print("--- DIGITAL ACTIVES ---")
    for active_id, info in list(digital_actives.items())[:5]:
        print(f"ID: {active_id}, Name: {info.get('name')}, Enabled: {info.get('enabled')}")
        
    print("\n--- TURBO ACTIVES ---")
    for active_id, info in list(turbo_actives.items())[:5]:
        print(f"ID: {active_id}, Name: {info.get('name')}, Enabled: {info.get('enabled')}")

if __name__ == "__main__":
    extract_details()
