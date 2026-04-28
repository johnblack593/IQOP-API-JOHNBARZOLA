import time
import os
from iqoptionapi.stable_api import IQ_Option

def test_trailing():
    email = os.environ.get("IQ_EMAIL", "your_email")
    password = os.environ.get("IQ_PASSWORD", "your_password")
    
    api = IQ_Option(email, password)
    api.connect()
    api.change_balance("PRACTICE")
    
    # Open a CFD position to test
    # Note: Replace with actual active and params valid for your account
    active = "EURUSD" 
    print(f"Opening test CFD position on {active}...")
    
    # Simple buy for testing
    status, order_id = api.buy_order(
        instrument_type="forex",
        active=active,
        direction="buy",
        margin=1,
        leverage=50
    )
    
    if status:
        print(f"Position opened: {order_id}")
        time.sleep(2)
        
        print("Setting trailing stop...")
        api.set_trailing_stop(order_id)
        
        time.sleep(2)
        print("Setting breakeven...")
        api.set_breakeven(order_id, profit_offset=0.1)
        
        time.sleep(5)
        # Verify state (would usually wait for position-changed event)
        
    api.close()

if __name__ == "__main__":
    test_trailing()
