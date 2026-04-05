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

class TestSuite_00_Connection(unittest.TestCase):
    """Module 0: Authentication, Connection & Session Management"""

    @classmethod
    def setUpClass(cls):
        if not EMAIL or not PASSWORD:
            raise unittest.SkipTest("IQ_EMAIL / IQ_PASSWORD not set")
        cls.api = IQ_Option(EMAIL, PASSWORD)
        cls.api.connect()
        cls.api.change_balance("PRACTICE")
        log.info("═══ MODULE 0: Connection & Auth ═══")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'api') and hasattr(cls.api, 'api'):
            cls.api.api.close()

    def test_01_connection_established(self):
        """Verify WebSocket connection is alive"""
        result = self.api.check_connect()
        self.assertTrue(result, "WebSocket connection should be established")
        log.info("✅ 0.1 WebSocket connection: ACTIVE")

    def test_02_server_timestamp(self):
        """Verify server timestamp is synced"""
        ts = self.api.get_server_timestamp()
        self.assertIsNotNone(ts, "Server timestamp should not be None")
        self.assertIsInstance(ts, (int, float), "Timestamp should be numeric")
        # Should be within ~60 seconds of local time
        diff = abs(time.time() - ts)
        self.assertLess(diff, 60, f"Server time drift too large: {diff}s")
        log.info(f"✅ 0.2 Server timestamp synced (drift: {diff:.2f}s)")

    def test_03_balance_retrieval(self):
        """Verify practice balance can be fetched"""
        balance = self.api.get_balance()
        self.assertIsNotNone(balance, "Balance should not be None")
        self.assertIsInstance(balance, (int, float), "Balance must be numeric")
        self.assertGreater(balance, 0, "Practice balance should be > 0")
        log.info(f"✅ 0.3 Practice balance: ${balance:,.2f}")

    def test_04_balance_mode(self):
        """Verify current balance mode is PRACTICE"""
        mode = self.api.get_balance_mode()
        self.assertIn(mode, ["PRACTICE", 4], "Should be in PRACTICE mode")
        log.info(f"✅ 0.4 Balance mode: PRACTICE (raw={mode})")

    def test_05_balance_id(self):
        """Verify balance_id is assigned"""
        balance_id = self.api.get_balance_id()
        self.assertIsNotNone(balance_id, "Balance ID should not be None")
        log.info(f"✅ 0.5 Balance ID: {balance_id}")

    def test_06_currency(self):
        """Verify account currency is retrievable"""
        currency = self.api.get_currency()
        self.assertIsNotNone(currency, "Currency should not be None")
        log.info(f"✅ 0.6 Account currency: {currency}")

    def test_07_profile_data(self):
        """Verify profile async data retrieval works"""
        self.api.get_profile_ansyc()
        time.sleep(1)
        profile = getattr(self.api.api, 'profile', None)
        self.assertIsNotNone(profile, "Profile object should exist")
        log.info(f"✅ 0.7 Profile data loaded successfully")

