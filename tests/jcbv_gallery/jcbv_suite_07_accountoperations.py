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

class TestSuite_07_AccountOperations(unittest.TestCase):
    """Module 7: Account Operations — Balance Reset, Mode Switch"""

    @classmethod
    def setUpClass(cls):
        if not EMAIL or not PASSWORD:
            raise unittest.SkipTest("IQ_EMAIL / IQ_PASSWORD not set")
        cls.api = IQ_Option(EMAIL, PASSWORD)
        cls.api.connect()
        cls.api.change_balance("PRACTICE")
        log.info("═══ MODULE 7: Account Operations ═══")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'api') and hasattr(cls.api, 'api'):
            cls.api.api.close()

    def test_01_reset_practice_balance(self):
        """Reset practice balance back to default"""
        self.api.reset_practice_balance()
        time.sleep(2)
        balance = self.api.get_balance()
        self.assertIsNotNone(balance)
        self.assertGreaterEqual(balance, 9900, "Balance should be ~$10,000 after reset")
        log.info(f"✅ 7.1 Practice balance reset: ${balance:,.2f}")

    def test_02_switch_to_practice(self):
        """Switch to PRACTICE mode and verify"""
        self.api.change_balance("PRACTICE")
        mode = self.api.get_balance_mode()
        self.assertIn(mode, ["PRACTICE", 4])
        log.info(f"✅ 7.2 Switched to PRACTICE mode: {mode}")

    def test_03_get_balances_list(self):
        """Retrieve all account balances (practice + real)"""
        balances = self.api.get_balances()
        self.assertIsNotNone(balances, "Balances list should not be None")
        log.info(f"✅ 7.3 Balances list retrieved: {type(balances).__name__}")

    def test_04_overnight_fee(self):
        """Check overnight fee for forex"""
        fee = self.api.get_overnight_fee("forex", "EURUSD")
        if fee is not None:
            log.info(f"✅ 7.4 Overnight fee (EURUSD forex): {fee}")
        else:
            log.warning("⚠️ 7.4 Overnight fee returned None")

    def test_05_commission_data(self):
        """Subscribe and check commission data"""
        self.api.subscribe_commission_changed("binary-option")
        time.sleep(1)
        commission = self.api.get_commission_change("binary-option")
        self.api.unsubscribe_commission_changed("binary-option")
        if commission is not None:
            log.info(f"✅ 7.5 Commission data retrieved")
        else:
            log.warning("⚠️ 7.5 Commission data returned None")

