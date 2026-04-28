import json
import time

def find_open_digital():
    with open("full_init.json", "r") as f:
        data = json.load(f)
    
    now = time.time()
    digital_actives = data.get("digital", {}).get("actives", {})
    
    open_assets = []
    for active_id, info in digital_actives.items():
        name = info.get("name", "").replace("front.", "")
        enabled = info.get("enabled", False)
        suspended = info.get("is_suspended", False)
        
        # Check schedule
        is_open = False
        schedule = info.get("schedule", [])
        for s in schedule:
            if s[0] < now < s[1]:
                is_open = True
                break
        
        if enabled and not suspended and is_open:
            open_assets.append(name)
            
    print(f"Open Digital Assets: {open_assets}")

if __name__ == "__main__":
    find_open_digital()
