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

class TestSuite_08_AssetResolution(unittest.TestCase):
    """Module 8: Dynamic Asset Resolution & Name Mapping"""

    @classmethod
    def setUpClass(cls):
        if not EMAIL or not PASSWORD:
            raise unittest.SkipTest("IQ_EMAIL / IQ_PASSWORD not set")
        cls.api = IQ_Option(EMAIL, PASSWORD)
        cls.api.connect()
        cls.api.change_balance("PRACTICE")
        log.info("═══ MODULE 8: Asset Resolution ═══")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'api') and hasattr(cls.api, 'api'):
            cls.api.api.close()

    def test_01_name_by_active_id(self):
        """Resolve asset name from numeric ID"""
        name = self.api.get_name_by_activeId(1)
        self.assertIsNotNone(name, "Name for activeId=1 should exist")
        # API returns display name 'EUR/USD' not opcode 'EURUSD'
        self.assertIn("EUR", name.upper(), "activeId 1 should contain EUR")
        self.assertIn("USD", name.upper(), "activeId 1 should contain USD")
        log.info(f"✅ 8.1 ActiveId 1 → {name}")

    def test_02_opcode_to_name(self):
        """Convert opcode back to name"""
        name = self.api.opcode_to_name(1)
        if name:
            log.info(f"✅ 8.2 Opcode 1 → {name}")
        else:
            log.warning("⚠️ 8.2 Opcode 1 returned None")

    def test_03_dynamic_actives_catalog(self):
        """Verify the live asset catalog was loaded during connect()"""
        from iqoptionapi.core.constants import ACTIVES
        self.assertGreater(len(ACTIVES), 50, 
                          f"ACTIVES catalog too small: {len(ACTIVES)}")
        log.info(f"✅ 8.3 Dynamic ACTIVES catalog: {len(ACTIVES)} assets loaded")

    def test_04_update_actives_opcode(self):
        """Trigger a manual update of ACTIVES OPCODE"""
        self.api.update_ACTIVES_OPCODE()
        actives = self.api.get_all_ACTIVES_OPCODE()
        self.assertIsNotNone(actives)
        self.assertGreater(len(actives), 0)
        log.info(f"✅ 8.4 ACTIVES OPCODE updated: {len(actives)} instruments")



