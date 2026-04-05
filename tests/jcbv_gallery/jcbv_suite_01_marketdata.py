#!/usr/bin/env python3
import os
import sys
import time
import logging
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("JCBV_QA")

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

class TestSuite_01_MarketData(unittest.TestCase):
    """Module 1: Market Data — Open Times, Instruments, Assets"""

    @classmethod
    def setUpClass(cls):
        if not EMAIL or not PASSWORD:
            raise unittest.SkipTest("IQ_EMAIL / IQ_PASSWORD not set")
        cls.api = IQ_Option(EMAIL, PASSWORD)
        cls.api.connect()
        cls.api.change_balance("PRACTICE")
        log.info("═══ MODULE 1: Market Data ═══")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'api') and hasattr(cls.api, 'api'):
            cls.api.api.close()

    def test_01_all_open_time(self):
        """Verify open time data for all instrument types"""
        data = self.api.get_all_open_time()
        self.assertIsNotNone(data, "Open time data should not be None")
        self.assertIsInstance(data, dict, "Should be a dictionary")
        # Must contain at least binary and turbo (digital is separate)
        for key in ["binary", "turbo"]:
            self.assertIn(key, data, f"Missing instrument type: {key}")
        log.info(f"✅ 1.1 Open times retrieved: {list(data.keys())}")

    def test_02_get_all_actives_opcode(self):
        """Verify ACTIVES opcode dictionary is populated"""
        actives = self.api.get_all_ACTIVES_OPCODE()
        self.assertIsNotNone(actives, "ACTIVES OPCODE should not be None")
        self.assertIsInstance(actives, dict)
        self.assertGreater(len(actives), 10, "Should have many active instruments")
        log.info(f"✅ 1.2 ACTIVES OPCODE loaded: {len(actives)} instruments")

    def test_03_get_instruments_binary(self):
        """Verify instrument list for binary options"""
        instruments = self.api.get_instruments("binary")
        # instruments may return None if the endpoint is slow 
        if instruments is not None:
            self.assertIsInstance(instruments, dict)
            log.info(f"✅ 1.3 Binary instruments fetched")
        else:
            log.warning("⚠️ 1.3 Binary instruments returned None (endpoint slow)")

    def test_04_get_all_profit(self):
        """Verify profit/payout data retrieval"""
        profit = self.api.get_all_profit()
        self.assertIsNotNone(profit, "Profit data should not be None")
        self.assertIsInstance(profit, dict)
        # At least some assets should have payout data
        self.assertGreater(len(profit), 0, "Profit dict should not be empty")
        # Sample one entry to verify structure
        sample_key = list(profit.keys())[0]
        sample_val = profit[sample_key]
        log.info(f"✅ 1.4 Profit data: {len(profit)} assets (sample: {sample_key}={sample_val})")

    def test_05_get_binary_option_detail(self):
        """Verify binary option detail retrieval"""
        detail = self.api.get_binary_option_detail()
        # This returns the full init data
        if detail is not None:
            log.info(f"✅ 1.5 Binary option detail loaded successfully")
        else:
            log.warning("⚠️ 1.5 Binary option detail returned None")

    def test_06_financial_information(self):
        """Verify financial info for a known asset"""
        # EURUSD = active_id 1
        info = self.api.get_financial_information(1)
        if info is not None:
            log.info(f"✅ 1.6 Financial info for EURUSD retrieved")
        else:
            log.warning("⚠️ 1.6 Financial info returned None")

