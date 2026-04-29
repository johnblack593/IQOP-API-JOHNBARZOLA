import os
import time
import json
import logging
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.core.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = get_logger(__name__)

def certify_digital():
    api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
    # RE-CERTI: Usamos el SSID capturado manualmente para evadir los timeouts de auth
    SSID = "05ac28045097edb0fcde0d87e0ce207q"
    status, reason = api.connect(ssid=SSID)
    
    if not status:
        print(f"Connection failed: {reason}")
        return


    api.change_balance("PRACTICE")
    time.sleep(2)

    print("--- STEP 0: Initialization ---")
    api.get_all_init_v2()
    api.get_all_open_time() 
    
    print("--- STEP 1: get_instruments('digital-option') ---")
    insts = api.get_instruments('digital-option')
    if insts and "instruments" in insts:
        print(f"Found {len(insts['instruments'])} instruments")
    else:
        print("FAIL: No instruments found")

    # --- STEP 2: get_digital_underlying_list_data() ---
    # print("\n--- STEP 2: get_digital_underlying_list_data() ---")
    # underlying = api.get_digital_underlying_list_data()
    # if underlying:
    #     print(f"Found {len(underlying)} underlying assets")
    # else:
    #     print("FAIL: No underlying found")

    asset = "EURUSD-OTC"
    print(f"\n--- STEP 3: buy_digital_spot_v2({asset}, 1, 'call', 1) ---")
    status, order_id = api.buy_digital_spot_v2(asset, 1, "call", 1)

    
    if status:
        print(f"SUCCESS: order_id={order_id}")
    else:
        print(f"FAIL: {order_id}")
        return

    print("\n--- STEP 4: check_win_digital_v2(order_id) ---")
    print("Waiting for trade result...")
    result, profit = api.check_win_digital_v2(order_id, timeout=150)
    
    if result:
        print(f"RESULT: Win? {result}, Profit: {profit}")
    else:
        print("FAIL: check_win_digital_v2 returned False/None (timeout or error)")

    api.close()

if __name__ == "__main__":
    certify_digital()

