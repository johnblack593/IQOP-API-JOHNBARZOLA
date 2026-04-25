import os
import time
import logging
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

import websocket
websocket.enableTrace(True)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_trade():
    load_dotenv()
    api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
    api.connect()
    api.change_balance("PRACTICE")
    
    # instrument_id format: do{ACTIVE}{YYYYMMDDHHII}PT{M}M{ACTION}SPT
    # EURUSD-OTC -> EURUSD
    # 1 minute -> PT1M
    # CALL -> C
    
    # Use a future expiration (e.g. 2 minutes from now)
    now = time.time()
    # Align to next minute
    exp = (int(now) // 60 + 2) * 60
    import datetime
    date_str = datetime.datetime.utcfromtimestamp(exp).strftime("%Y%m%d%H%M")
    
    # Try EURUSD-OTC format
    check, order_id = api.buy_digital_spot_v2("EURUSD-OTC", 1, "call", 1)
    print(f"Result: {check}, OrderID: {order_id}")
    
    if check:
        print("Waiting for result...")
        res = api.check_win_v4(order_id)
        print(f"Win check: {res}")
    
    api.api.close()

if __name__ == "__main__":
    test_trade()
