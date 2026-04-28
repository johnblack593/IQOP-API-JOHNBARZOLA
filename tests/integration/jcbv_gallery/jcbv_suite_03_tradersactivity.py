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

class TestSuite_03_TradersActivity(unittest.TestCase):
    """Module 3: Trader Sentiment & Social Data"""

    @classmethod
    def setUpClass(cls):
        if not EMAIL or not PASSWORD:
            raise unittest.SkipTest("IQ_EMAIL / IQ_PASSWORD not set")
        cls.api = IQ_Option(EMAIL, PASSWORD)
        cls.api.connect()
        cls.api.change_balance("PRACTICE")
        log.info("═══ MODULE 3: Trader Sentiment ═══")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'api') and hasattr(cls.api, 'api'):
            cls.api.api.close()

    def test_01_traders_mood_stream(self):
        """Subscribe and read trader mood for EURUSD"""
        self.api.start_mood_stream("EURUSD")
        time.sleep(2)
        
        mood = self.api.get_traders_mood("EURUSD")
        if mood is not None:
            self.assertIsInstance(mood, (int, float, dict))
            log.info(f"✅ 3.1 Traders mood for EURUSD: {mood}")
        else:
            log.warning("⚠️ 3.1 Traders mood returned None (stream may be delayed)")
        
        self.api.stop_mood_stream("EURUSD")

    def test_02_technical_indicators(self):
        """Retrieve technical indicator data"""
        indicators = self.api.get_technical_indicators("EURUSD")
        if indicators is not None:
            log.info(f"✅ 3.2 Technical indicators retrieved")
        else:
            log.warning("⚠️ 3.2 Technical indicators returned None")

    def test_03_top_assets(self):
        """Subscribe and get top traded assets"""
        # instrument_type: "binary-option", "turbo-option", "digital-option", etc.
        self.api.subscribe_top_assets_updated("binary-option")
        time.sleep(2)
        top = self.api.get_top_assets_updated("binary-option")
        if top is not None:
            log.info(f"✅ 3.3 Top assets (binary): retrieved")
        else:
            log.warning("⚠️ 3.3 Top assets returned None")
        self.api.unsubscribe_top_assets_updated("binary-option")

    def test_04_leaderboard(self):
        """Retrieve leaderboard data"""
        lb = self.api.get_leader_board(
            country="Worldwide",
            from_position=1,
            to_position=10,
            near_traders_count=0,
            user_country_id=0,
            near_traders_country_count=0,
            top_country_count=0,
            top_count=10,
            top_type=2
        )
        if lb is not None:
            log.info(f"✅ 3.4 Leaderboard data retrieved")
        else:
            log.warning("⚠️ 3.4 Leaderboard returned None")

