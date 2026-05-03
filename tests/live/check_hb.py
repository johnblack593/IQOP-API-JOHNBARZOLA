from iqoptionapi.stable_api import IQ_Option
import time
import os
from dotenv import load_dotenv

load_dotenv()

email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

api = IQ_Option(email, password, active_account_type="PRACTICE")
check, reason = api.connect()

if check:
    print("Connected. Waiting 30s for heartbeats...")
    # El heartbeat se envía cada 5s por defecto en JCBV-NEXUS
    time.sleep(30)
    
    if os.path.exists("ws_debug.log"):
        with open("ws_debug.log", "r") as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"RAW: {line.strip()}")
    
    api.close()
else:
    print(f"Failed: {reason}")
