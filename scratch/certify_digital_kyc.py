# scratch/certify_digital_kyc.py
import os, time, json
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
check, _ = api.connect()
assert check
api.change_balance("PRACTICE")
time.sleep(2)

# XRPUSD-OTC (ID 2107) is known to be open and working for Digital
target = "XRPUSD-OTC"
print(f"Target: {target}")

# Forzamos que el SDK sepa que es digital al menos para esta prueba
# (Aunque buy_digital_spot_v2 lo deduce del active_id si está en ACTIVES)
status, order_id = api.buy_digital_spot_v2(target, 1, "call", 1)
print(f"Result: status={status}, order_id={order_id}")

if status:
    print(f"✅ SUCCESS! Order ID: {order_id}")
    time.sleep(70)
    profit, res = api.check_win_digital_v2(order_id)
    print(f"Profit: {profit}, Result: {res}")
    
    with open("scratch/digital_certification_result.json", "w") as f:
        json.dump({"asset": target, "order_id": order_id, "profit": profit, "result": res}, f, indent=2)
else:
    print("❌ FAILED")

api.close()
