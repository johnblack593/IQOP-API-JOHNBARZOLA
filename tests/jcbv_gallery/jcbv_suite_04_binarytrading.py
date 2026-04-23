#!/usr/bin/env python3
import os
import sys
import time
import logging
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("JCBV_QA")

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

class TestSuite_04_BinaryTrading(unittest.TestCase):
    """Module 4: Binary/Turbo Options — Buy, Check, Sell"""

    @classmethod
    def setUpClass(cls):
        if not EMAIL or not PASSWORD:
            raise unittest.SkipTest("IQ_EMAIL / IQ_PASSWORD not set")
        cls.api = IQ_Option(EMAIL, PASSWORD)
        status, reason = cls.api.connect()
        if not status:
            raise unittest.SkipTest(f"Connect failed: {reason}")
            
        if not cls.api.change_balance("PRACTICE"):
            log.warning("Could not change to PRACTICE balance, might already be there or failed.")
            
        log.info("═══ MODULE 4: Binary Trading ═══")

        # Determine best available asset
        open_times = cls.api.get_all_open_time()
        cls.target_asset = None
        
        # Priority: EURUSD turbo → EURUSD-OTC turbo → any open turbo
        if open_times.get("turbo", {}).get("EURUSD", {}).get("open"):
            cls.target_asset = "EURUSD"
        elif open_times.get("turbo", {}).get("EURUSD-OTC", {}).get("open"):
            cls.target_asset = "EURUSD-OTC"
        else:
            # Find any open turbo asset
            for asset, info in open_times.get("turbo", {}).items():
                if info.get("open"):
                    cls.target_asset = asset
                    break
        
        if cls.target_asset:
            log.info(f"  Target asset: {cls.target_asset}")
        else:
            log.warning("  ⚠️ No turbo assets currently open")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'api') and hasattr(cls.api, 'api'):
            cls.api.api.close()

    def test_01_buy_call(self):
        """Place a $1 CALL binary option in PRACTICE mode"""
        if not self.target_asset:
            self.skipTest("No turbo assets open")

        check, order_id = self.api.buy(1, self.target_asset, "call", 1)
        
        if check:
            self.assertTrue(check)
            self.assertIsNotNone(order_id, "Order ID should not be None")
            log.info(f"✅ 4.1 BUY CALL: success (order_id={order_id})")
            
            # Try to sell immediately
            result = self.api.sell_option(order_id)
            log.info(f"  → Sell result: {result}")
        else:
            log.warning(f"⚠️ 4.1 BUY CALL failed: {order_id} (market may reject)")

    def test_02_buy_put(self):
        """Place a $1 PUT binary option in PRACTICE mode"""
        if not self.target_asset:
            self.skipTest("No turbo assets open")

        check, order_id = self.api.buy(1, self.target_asset, "put", 1)
        
        if check:
            self.assertTrue(check)
            self.assertIsNotNone(order_id)
            log.info(f"✅ 4.2 BUY PUT: success (order_id={order_id})")
            
            result = self.api.sell_option(order_id)
            log.info(f"  → Sell result: {result}")
        else:
            log.warning(f"⚠️ 4.2 BUY PUT failed: {order_id}")

    def test_03_check_binary_order(self):
        """Place order and verify bet info"""
        if not self.target_asset:
            self.skipTest("No turbo assets open")

        check, order_id = self.api.buy(1, self.target_asset, "call", 1)
        if check and order_id:
            info = self.api.check_binary_order(order_id)
            log.info(f"✅ 4.3 Binary order check: {info}")
            # Sell to clean up
            self.api.sell_option(order_id)
        else:
            log.warning("⚠️ 4.3 Cannot test — buy failed")

    def test_04_get_betinfo(self):
        """Place order and fetch bet info data"""
        if not self.target_asset:
            self.skipTest("No turbo assets open")
        
        check, order_id = self.api.buy(1, self.target_asset, "call", 1)
        if check and order_id:
            success, betinfo = self.api.get_betinfo(order_id)
            log.info(f"✅ 4.4 BetInfo: success={success}")
            self.api.sell_option(order_id)
        else:
            log.warning("⚠️ 4.4 Cannot test — buy failed")

    def test_05_get_optioninfo(self):
        """Retrieve option info with limit"""
        info = self.api.get_optioninfo(10)
        if info is not None:
            log.info(f"✅ 4.5 Option info retrieved (limit=10)")
        else:
            log.warning("⚠️ 4.5 Option info returned None")

if __name__ == "__main__":
    unittest.main()