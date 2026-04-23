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

class TestSuite_05_DigitalTrading(unittest.TestCase):
    """Module 5: Digital Options — Spots, Strikes, Payouts"""

    @classmethod
    def setUpClass(cls):
        if not EMAIL or not PASSWORD:
            raise unittest.SkipTest("IQ_EMAIL / IQ_PASSWORD not set")
        cls.api = IQ_Option(EMAIL, PASSWORD)
        cls.api.connect()
        cls.api.change_balance("PRACTICE")
        log.info("═══ MODULE 5: Digital Options ═══")

        # Check if digital is open
        open_times = cls.api.get_all_open_time()
        cls.digital_asset = None
        
        for asset in ["EURUSD", "EURUSD-OTC"]:
            if open_times.get("digital", {}).get(asset, {}).get("open"):
                cls.digital_asset = asset
                break
        
        if not cls.digital_asset:
            for asset, info in open_times.get("digital", {}).items():
                if info.get("open"):
                    cls.digital_asset = asset
                    break

        if cls.digital_asset:
            log.info(f"  Digital target: {cls.digital_asset}")
        else:
            log.warning("  ⚠️ No digital assets currently open")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'api') and hasattr(cls.api, 'api'):
            cls.api.api.close()

    def test_01_digital_underlying_list(self):
        """Fetch digital underlying list"""
        data = self.api.get_digital_underlying_list_data()
        if data is not None:
            self.assertIsInstance(data, (dict, list))
            log.info(f"✅ 5.1 Digital underlying list retrieved")
        else:
            log.warning("⚠️ 5.1 Digital underlying list returned None")

    def test_02_digital_payout(self):
        """Check digital option payout for an asset"""
        if not self.digital_asset:
            self.skipTest("No digital assets open")

        payout = self.api.get_digital_payout(self.digital_asset)
        if payout is not None:
            log.info(f"✅ 5.2 Digital payout for {self.digital_asset}: {payout}%")
        else:
            log.warning(f"⚠️ 5.2 Digital payout returned None")

    def test_03_strike_list(self):
        """Fetch strike list for digital option"""
        if not self.digital_asset:
            self.skipTest("No digital assets open")
        
        raw, strikes = self.api.get_strike_list(self.digital_asset, 1)
        if strikes is not None:
            self.assertIsInstance(strikes, dict)
            log.info(f"✅ 5.3 Strike list: {len(strikes)} strike prices")
        else:
            log.warning("⚠️ 5.3 Strike list returned None")

    def test_04_buy_digital_spot(self):
        """Place a $1 digital option spot trade"""
        if not self.digital_asset:
            self.skipTest("No digital assets open")

        check, order_id = self.api.buy_digital_spot(
            self.digital_asset, 1, "call", 1
        )
        if check:
            self.assertIsNotNone(order_id)
            log.info(f"✅ 5.4 Digital BUY CALL: success (order_id={order_id})")
            # Try closing
            self.api.close_digital_option(order_id)
        else:
            log.warning(f"⚠️ 5.4 Digital BUY failed: {order_id}")

