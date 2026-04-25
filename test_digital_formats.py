import os
import time
import datetime
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

def test_formats():
    load_dotenv()
    api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
    api.connect()
    api.change_balance("PRACTICE")
    
    asset = "GBPUSD-OTC"
    active_id = 81
    duration = 1
    amount = 1
    action = "C" # Call
    
    now = time.time()
    exp = (int(now) // 60 + 2) * 60
    date_str = datetime.datetime.utcfromtimestamp(exp).strftime("%Y%m%d%H%M")
    
    # Format list to try
    formats = [
        f"do{asset}{date_str}PT{duration}M{action}SPT",
        f"do{asset.replace('-OTC', '')}{date_str}PT{duration}M{action}SPT",
        f"do{asset.replace('-', '')}{date_str}PT{duration}M{action}SPT",
        f"digital-option.{asset}{date_str}PT{duration}M{action}SPT",
    ]
    
    for instrument_id in formats:
        print(f"\n--- Testing Format: {instrument_id} ---")
        # Try v2.0
        print("Trying v2.0...")
        check, order_id = api.buy_digital_spot_v2(asset, amount, "call", duration)
        # Note: buy_digital_spot_v2 uses internal logic, we need to bypass it to test CUSTOM formats
        
        # Direct call to API
        data = {
            "name": "digital-options.place-digital-option",
            "version": "2.0",
            "body": {
                "instrument_id": instrument_id,
                "active_id": active_id,
                "amount": str(amount),
                "user_balance_id": int(api.api.balance_id)
            }
        }
        api.api.send_websocket_request(name="sendMessage", msg=data)
        
        # Wait for response in logs (we rely on websocket trace)
        time.sleep(5)

    api.api.close()

if __name__ == "__main__":
    import websocket
    websocket.enableTrace(True)
    test_formats()
