import json, os

def sanitize_json(filepath):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found, skipping.")
        return
    
    with open(filepath, "r") as f:
        try:
            data = json.load(f)
        except:
            print(f"Error loading {filepath}")
            return
            
    # Remover campos sensibles si existen
    sensitives = ["account_id", "user_id", "session", "email", "ssid", "token"]
    
    # Si es un dict, limpiar raíz
    if isinstance(data, dict):
        for key in sensitives:
            if key in data:
                print(f"Removing {key} from {filepath}")
                data.pop(key, None)
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    print(f"Sanitized {filepath}")

sanitize_json("open_time.json")
sanitize_json("examples/debug_actives_kyc_map.json")
