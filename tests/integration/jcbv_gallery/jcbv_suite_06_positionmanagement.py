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

class TestSuite_06_PositionManagement(unittest.TestCase):
    """Module 6: Position & Order Management"""

    @classmethod
    def setUpClass(cls):
        if not EMAIL or not PASSWORD:
            raise unittest.SkipTest("IQ_EMAIL / IQ_PASSWORD not set")
        cls.api = IQ_Option(EMAIL, PASSWORD)
        cls.api.connect()
        cls.api.change_balance("PRACTICE")
        log.info("═══ MODULE 6: Position Management ═══")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'api') and hasattr(cls.api, 'api'):
            cls.api.api.close()

    def test_01_get_positions_binary(self):
        """Retrieve open binary positions"""
        positions = self.api.get_positions("multi-option")
        # May be None or empty if no active positions
        log.info(f"✅ 6.1 Binary positions: {type(positions).__name__}")

    def test_02_get_positions_digital(self):
        """Retrieve open digital positions"""
        positions = self.api.get_positions("digital-option")
        log.info(f"✅ 6.2 Digital positions: {type(positions).__name__}")

    def test_03_get_positions_forex(self):
        """Retrieve open forex positions"""
        positions = self.api.get_positions("forex")
        log.info(f"✅ 6.3 Forex positions: {type(positions).__name__}")

    def test_04_get_positions_crypto(self):
        """Retrieve open crypto positions"""
        positions = self.api.get_positions("crypto")
        log.info(f"✅ 6.4 Crypto positions: {type(positions).__name__}")

    def test_05_get_position_history_binary(self):
        """Retrieve binary position history"""
        history = self.api.get_position_history("multi-option")
        log.info(f"✅ 6.5 Binary history: {type(history).__name__}")

    def test_06_get_pending_orders(self):
        """Retrieve pending orders"""
        pending = self.api.get_pending("multi-option")
        log.info(f"✅ 6.6 Pending orders: {type(pending).__name__}")

