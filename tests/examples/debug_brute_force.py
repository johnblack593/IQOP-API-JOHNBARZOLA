import os
import json
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
api.connect()

def test_payload(name, msg_dict):
    api.api.send_websocket_request(name, msg_dict)
    time.sleep(2)
    # the server responds with name="instruments" usually.
    # we can check api.api.instruments if it's cached, or we can just print the raw websocket dict.
    print(f"Sent {name} with {msg_dict}")

print("Testing instruments versions for CFD...")
# Testing generic request
api.api.send_websocket_request("sendMessage", {"name": "get-instruments", "version": "4.0", "body": {"type": "cfd"}})
time.sleep(1)
print("V4.0 CFD Response:", api.api.instruments)

api.api.send_websocket_request("sendMessage", {"name": "get-instruments", "version": "5.0", "body": {"type": "cfd"}})
time.sleep(1)
print("V5.0 CFD Response:", api.api.instruments)

api.api.send_websocket_request("sendMessage", {"name": "get-instruments", "version": "3.0", "body": {"type": "cfd"}})
time.sleep(1)
print("V3.0 CFD Response:", api.api.instruments)

api.api.send_websocket_request("sendMessage", {"name": "get-instruments", "version": "2.0", "body": {"type": "cfd"}})
time.sleep(1)
print("V2.0 CFD Response:", api.api.instruments)

api.api.send_websocket_request("sendMessage", {"name": "get-instruments", "version": "1.0", "body": {"type": "cfd"}})
time.sleep(1)
print("V1.0 CFD Response:", api.api.instruments)

api.close()
