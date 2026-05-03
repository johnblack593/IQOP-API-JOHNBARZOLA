import os
import time
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

print(f"Connecting as {email}...")
api = IQ_Option(email, password)
check, reason = api.connect()

if check:
    print("SUCCESS: Connected!")
    print(f"Server timestamp: {api.get_server_timestamp()}")
    api.close()
else:
    print(f"FAILURE: {reason}")
