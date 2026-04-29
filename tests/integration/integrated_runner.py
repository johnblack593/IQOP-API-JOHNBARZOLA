#!/usr/bin/env python3
import unittest
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    load_dotenv()
    print("=" * 72)
    print("  IQ OPTION API — JCBV EDITION")
    print("  TARGETED SUITE 04 RUNNER (Sprint 3)")
    print("=" * 72)

    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jcbv_gallery')
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=start_dir, pattern='jcbv_suite_04_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
