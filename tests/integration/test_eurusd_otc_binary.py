import os
import time
import json
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

def test_binary_otc():
    load_dotenv()
    
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    
    print(f"Connecting as {email}...")
    api = IQ_Option(email, password)
    check, reason = api.connect()
    
    if not check:
        print(f"Connection failed: {reason}")
        return

    api.change_balance("PRACTICE")
    print(f"Switched to PRACTICE. Current balance: {api.get_balance()}")

    asset = "EURUSD-OTC"
    amount = 1
    action = "call" # 'call'/'put'
    duration = 1 # minutes

    print(f"Placing binary trade: {asset} {amount}$ {action} {duration}min")
    check, id = api.buy(amount, asset, action, duration)
    
    if check:
        print(f"Trade placed successfully! ID: {id}")
        print("Waiting for result (max 120s)...")
        
        start_time = time.time()
        result = None
        while time.time() - start_time < 120:
            win_amount = api.check_win_v3(id)
            if win_amount is not None:
                result = win_amount
                break
            time.sleep(1)
            
        if result is not None:
            print(f"Trade finished! Result: {result}")
        else:
            print("Timeout waiting for result.")
    else:
        print(f"Failed to place trade: {id}")

    api.api.close()

if __name__ == "__main__":
    test_binary_otc()
