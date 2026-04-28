import os
import time
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()

def test_conn():
    api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
    status, reason = api.connect()
    print(f"Status: {status}, Reason: {reason}")
    if status:
        print("Connected successfully!")
        api.close()

if __name__ == "__main__":
    test_conn()
