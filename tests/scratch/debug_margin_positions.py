import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("IQ_EMAIL", "")
PASSWORD = os.getenv("IQ_PASSWORD", "")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.core.logger import get_logger

def main():
    iq = IQ_Option(EMAIL, PASSWORD)
    print("Connecting...")
    status, _ = iq.connect()
    if not status:
        print("Failed to connect")
        return

    try:
        iq.change_balance("PRACTICE")
    except Exception as e:
        print("Could not change balance:", e)

    print("\n--- Testing get-positions ---")
    iq.api.positions_event.clear()
    iq.api.get_positions("marginal-forex")
    iq.api.positions_event.wait(5)
    print("get-positions response:", iq.api.positions)

    print("\n--- Testing portfolio.get-positions v3.0 ---")
    iq.api.open_positions_event.clear()
    iq.api.send_websocket_request(
        name="sendMessage",
        msg={
            "name": "portfolio.get-positions",
            "version": "3.0",
            "body": {
                "instrument_type": "marginal-forex",
                "user_balance_id": iq.api.balance_id,
                "offset": 0,
                "limit": 100
            }
        }
    )
    iq.api.open_positions_event.wait(5)
    print("portfolio.get-positions response:", iq.api.open_positions.get("marginal-forex"))

    iq.close()

if __name__ == "__main__":
    main()

