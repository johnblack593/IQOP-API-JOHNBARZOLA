import time
import logging
from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.INFO)

def test_sync():
    # Use environment variables for safety or placeholders
    import os
    email = os.environ.get("IQ_EMAIL", "your_email")
    password = os.environ.get("IQ_PASSWORD", "your_password")
    
    api = IQ_Option(email, password)
    status, reason = api.connect()
    
    if not status:
        print(f"Login failed: {reason}")
        return

    print("Checking positions_state_data...")
    print(f"Sync complete: {len(api.positions_state_data)} positions found.")
    
    # Simulate disconnect
    print("Simulating disconnect...")
    api.api.websocket_client.wss.close()
    
    time.sleep(5) # Wait for auto-reconnect
    
    print(f"After reconnect, positions: {len(api.positions_state_data)}")
    
    api.close()

if __name__ == "__main__":
    test_sync()
