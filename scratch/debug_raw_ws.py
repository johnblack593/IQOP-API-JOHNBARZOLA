import os
import sys
import time
import json
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("IQ_EMAIL", "")
PASSWORD = os.getenv("IQ_PASSWORD", "")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from iqoptionapi.stable_api import IQ_Option
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

def main():
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()

    def interceptor(message):
        try:
            msg_str = str(message)
            if len(msg_str) > 50 and "heartbeat" not in msg_str and "timeSync" not in msg_str and "client-price" not in msg_str:
                print(f"\n[INTERCEPT len={len(msg_str)}] >>", msg_str[:1500])
        except:
            pass

    # Monkey patch to see all messages
    original_on_message = iq.api.websocket_client.wss.on_message
    def new_on_message(wss, message):
        interceptor(message)
        original_on_message(wss, message)
    iq.api.websocket_client.wss.on_message = new_on_message

    print("\n\n=== SENDING GET AVAILABLE LEVERAGES (forex, 2.0) ===")
    iq.api.send_websocket_request(
        name="sendMessage",
        msg={
            "name": "get-available-leverages",
            "version": "2.0",
            "body": {
                "instrument_type": "forex",
                "actives": [1]
            }
        }
    )
    time.sleep(3)

    print("\n\n=== SENDING PORTFOLIO GET POSITIONS (marginal-forex, 4.0) ===")
    iq.api.send_websocket_request(
        name="sendMessage",
        msg={
            "name": "portfolio.get-positions",
            "version": "4.0",
            "body": {
                "instrument_type": "marginal-forex",
                "user_balance_id": iq.api.balance_id,
                "offset": 0,
                "limit": 100
            }
        }
    )
    time.sleep(5)

    print("\n\n=== SENDING PORTFOLIO GET POSITIONS (marginal-forex, 1.0) ===")
    iq.api.send_websocket_request(
        name="sendMessage",
        msg={
            "name": "portfolio.get-positions",
            "version": "1.0",
            "body": {
                "instrument_type": "marginal-forex",
                "user_balance_id": iq.api.balance_id,
                "offset": 0,
                "limit": 100
            }
        }
    )
    time.sleep(5)
    iq.close()

if __name__ == "__main__":
    main()
