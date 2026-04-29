import json
import os

def compare():
    # Load new open_time.json
    with open('open_time.json', 'r') as f:
        new_data = json.load(f)

    print("--- DIGITAL OPTIONS AUDIT ---")
    if "digital" in new_data:
        print("[OK] 'digital' key found in open_time.json")
        digital_assets = new_data["digital"]
        open_digital = [k for k, v in digital_assets.items() if v.get("open")]
        print(f"Total digital assets: {len(digital_assets)}")
        print(f"Open digital assets: {len(open_digital)}")
        for asset in sorted(open_digital):
            print(f"  - {asset}")
    else:
        print("[FAIL] 'digital' key still missing from open_time.json")


    print("\n--- CFD AUDIT (KYC BLOCK CHECK) ---")
    cfd_assets = new_data.get("cfd", {})
    
    candidates = [
        "MSFT", "AAPL", "GOOGL", "BABA", "SNAP", "CISCO", "INTC", "NIKE", 
        "BIDU", "MORSTAN", "AIG", "USO/USD", "NFLX/AMZN", "XAUUSD", 
        "NVDA/AMD", "META/GOOGLE", "GOOGLE/MSFT", "INTEL/IBM",
        "NFLX", "NVDA", "AMD", "TSLA", "WMT", "V", "JPM", "Crude Oil", "Brent Oil"
    ]

    print(f"{'Asset':<20} | {'Status':<10}")
    print("-" * 35)
    for asset in candidates:
        status = "NOT FOUND"
        if asset in cfd_assets:
            status = "OPEN" if cfd_assets[asset].get("open") else "CLOSED"
        else:
            # Try to find by partial name
            for k in cfd_assets:
                if asset in k:
                    status = "OPEN" if cfd_assets[k].get("open") else "CLOSED"
                    asset = f"{asset} ({k})"
                    break
        print(f"{asset:<20} | {status:<10}")

if __name__ == "__main__":
    compare()
