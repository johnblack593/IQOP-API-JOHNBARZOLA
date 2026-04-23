import os
import time
import logging
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("S2_VALIDATION")

def test_digital_trade():
    load_dotenv()
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    
    iq = IQ_Option(email, password)
    status, reason = iq.connect()
    
    if not status:
        logger.error(f"Connect failed: {reason}")
        return

    logger.info("Connected. Discovering assets...")
    data = iq.get_all_open_time()
    digital_assets = data.get("digital", {})
    open_digitals = [k for k, v in digital_assets.items() if v.get("open")]
    
    if not open_digitals:
        logger.warning("No open digital assets found. Skipping trade test.")
        # Try binary if no digital
        binary_assets = data.get("binary", {})
        open_binaries = [k for k, v in binary_assets.items() if v.get("open")]
        if not open_binaries:
             iq.api.close()
             return
        asset = open_binaries[0]
        logger.info(f"Placing binary trade for {asset}...")
        status, buy_id = iq.buy(1, asset, "call", 1)
        if status:
            logger.info(f"Binary Trade placed: {buy_id}. Waiting for result...")
            win, profit = iq.check_win_v2(buy_id)
            logger.info(f"Binary Trade result: {win}, profit: {profit}")
    else:
        asset = open_digitals[0]
        logger.info(f"Placing digital trade for {asset}...")
        status, buy_id = iq.buy_digital_v2(asset, 1, "call", 1)
        if status:
            logger.info(f"Digital Trade placed: {buy_id}. Waiting for result...")
            # S2-T3: Verify check_win_digital_v2
            win, profit = iq.check_win_digital_v2(buy_id)
            logger.info(f"Digital Trade result: {win}, profit: {profit}")

    # S2-T4: Memory test
    logger.info(f"Memory check - result_event_store size: {len(iq.api.result_event_store)}")
    logger.info(f"Memory check - position_changed_event_store size: {len(iq.api.position_changed_event_store)}")

    time.sleep(5)
    iq.api.close()

if __name__ == "__main__":
    test_digital_trade()
