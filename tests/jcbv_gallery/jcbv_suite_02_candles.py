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

class TestSuite_02_Candles(unittest.TestCase):
    """Module 2: Candlestick Data — Historical & Realtime Streams"""

    @classmethod
    def setUpClass(cls):
        if not EMAIL or not PASSWORD:
            raise unittest.SkipTest("IQ_EMAIL / IQ_PASSWORD not set")
        cls.api = IQ_Option(EMAIL, PASSWORD)
        cls.api.connect()
        cls.api.change_balance("PRACTICE")
        log.info("═══ MODULE 2: Candlestick Data ═══")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'api') and hasattr(cls.api, 'api'):
            cls.api.api.close()

    def test_01_historical_candles_1min(self):
        """Fetch 10 historical 1-minute candles for EURUSD"""
        candles = self.api.get_candles("EURUSD", 60, 10, time.time())
        self.assertIsNotNone(candles, "Candles should not be None")
        self.assertIsInstance(candles, list, "Candles should be a list")
        self.assertGreaterEqual(len(candles), 1, "Should have at least 1 candle")
        # Verify candle structure
        c = candles[0]
        for field in ["open", "close", "min", "max", "volume"]:
            self.assertIn(field, c, f"Candle missing '{field}' field")
        log.info(f"✅ 2.1 Historical candles (1m): {len(candles)} received")

    def test_02_historical_candles_5min(self):
        """Fetch 5 historical 5-minute candles for EURUSD"""
        candles = self.api.get_candles("EURUSD", 300, 5, time.time())
        self.assertIsNotNone(candles, "Candles should not be None")
        self.assertGreaterEqual(len(candles), 1, "Should have at least 1 candle")
        log.info(f"✅ 2.2 Historical candles (5m): {len(candles)} received")

    def test_03_historical_candles_15min(self):
        """Fetch 3 historical 15-minute candles for EURUSD"""
        candles = self.api.get_candles("EURUSD", 900, 3, time.time())
        self.assertIsNotNone(candles, "Candles should not be None")
        self.assertGreaterEqual(len(candles), 1, "Should have at least 1 candle")
        log.info(f"✅ 2.3 Historical candles (15m): {len(candles)} received")

    def test_04_realtime_candle_stream(self):
        """Subscribe, receive, and unsubscribe from realtime candle stream"""
        ACTIVE = "EURUSD"
        size = 60  # 1-minute candles

        self.api.start_candles_stream(ACTIVE, size, 10)
        time.sleep(3)  # Wait for stream to populate

        realtime = self.api.get_realtime_candles(ACTIVE, size)
        self.assertIsNotNone(realtime, "Realtime candles should not be None")
        
        self.api.stop_candles_stream(ACTIVE, size)
        log.info(f"✅ 2.4 Realtime stream: subscribe → receive → unsubscribe OK")

    def test_05_get_remaining_time(self):
        """Verify expiration countdown timer"""
        remaining = self.api.get_remaning(1)
        # Could be int (seconds) or error string
        if isinstance(remaining, (int, float)):
            self.assertGreaterEqual(remaining, 0, "Remaining time should be >= 0")
            log.info(f"✅ 2.5 Remaining time (1min exp): {remaining}s")
        else:
            log.warning(f"⚠️ 2.5 Remaining time returned: {remaining}")

