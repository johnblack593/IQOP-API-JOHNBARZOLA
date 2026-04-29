import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("IQ_EMAIL", "")
PASSWORD = os.getenv("IQ_PASSWORD", "")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from iqoptionapi.stable_api import IQ_Option

def main():
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()
    
    original_on_message = iq.api.websocket_client.wss.on_message
    def interceptor(wss, message):
        msg = str(message)
        if "tpsl" in msg or "close-position" in msg or "4000" in msg or "4101" in msg or "success" in msg:
            if len(msg) < 500:
                print(f"\n[SERVER] >> {msg}")
        original_on_message(wss, message)
    iq.api.websocket_client.wss.on_message = interceptor
    
    print("Balance:", iq.get_balance())

    print("1. Opening margin position...")
    status, order_id = iq.open_margin_position(
        instrument_type="forex",
        active_id=1,  # EURUSD
        amount=10,
        leverage=50,
        direction="buy"
    )
    print(f"Open: {status}, order_id={order_id}")
    real_order_id = order_id["id"] if isinstance(order_id, dict) else order_id
    time.sleep(2)
    
    # Force _resolve_margin_position_id to return BOTH
    positions = iq.get_open_positions("marginal-forex", timeout=5.0)
    uuid_id = None
    ext_id = None
    for p in positions:
        order_ids = []
        raw_event = p.get("raw_event", {})
        for k, v in raw_event.items():
            if isinstance(v, dict) and "order_ids" in v:
                order_ids.extend(v["order_ids"])
                
        if p.get("external_id") == real_order_id or real_order_id in order_ids:
            uuid_id = p.get("id")
            ext_id = p.get("external_id")
            break
            
    print(f"Resolved pos_id (UUID): {uuid_id}, external_id: {ext_id}")
    
    print("2. Try change-tpsl version 2.0 with int (external_id)")
    iq.api.send_websocket_request("sendMessage", {"name": "change-tpsl", "version": "2.0", "body": {"position_id": ext_id, "stop_lose_kind": "pnl", "stop_lose_value": 3}})
    time.sleep(2)

    print("3. Try change-tpsl version 3.0 with string (UUID)")
    print(f"UUID: {uuid_id}")
    
    iq.api.send_websocket_request("sendMessage", {"name": "change-tpsl", "version": "3.0", "body": {"position_id": uuid_id, "stop_lose_kind": "pnl", "stop_lose_value": 3}})
    time.sleep(2)
    
    print("4. Try change-tpsl version 4.0 with string (UUID)")
    iq.api.send_websocket_request("sendMessage", {"name": "change-tpsl", "version": "4.0", "body": {"position_id": uuid_id, "stop_lose_kind": "pnl", "stop_lose_value": 3}})
    time.sleep(2)
    
    print("5. Try marginal-forex.change-tpsl v2.0 with ext_id")
    iq.api.send_websocket_request("sendMessage", {"name": "marginal-forex.change-tpsl", "version": "2.0", "body": {"position_id": ext_id, "stop_lose_kind": "pnl", "stop_lose_value": 3}})
    time.sleep(2)
    
    print("6. Try marginal-forex.change-tpsl v3.0 with ext_id")
    iq.api.send_websocket_request("sendMessage", {"name": "marginal-forex.change-tpsl", "version": "3.0", "body": {"position_id": ext_id, "stop_lose_kind": "pnl", "stop_lose_value": 3}})
    time.sleep(2)
    
    print("7. Try change-tpsl v2.0 with ORDER_ID")
    iq.api.send_websocket_request("sendMessage", {"name": "change-tpsl", "version": "2.0", "body": {"position_id": real_order_id, "stop_lose_kind": "pnl", "stop_lose_value": 3}})
    time.sleep(2)


if __name__ == "__main__":
    main()
