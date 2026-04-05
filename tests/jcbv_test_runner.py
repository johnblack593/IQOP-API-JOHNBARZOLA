#!/usr/bin/env python3
import unittest
import sys
import os
from datetime import datetime

import logging

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    print("=" * 72)
    print("  IQ OPTION API — JCBV EDITION")
    print("  COMPREHENSIVE TEST GALLERY RUNNER")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)
    print()

    # Create root level logger to intercept anything unwanted, if desired
    # For now, let the individual files log their own

    # Discover tests from the jcbv_gallery directory
    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jcbv_gallery')
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=start_dir, pattern='jcbv_suite_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 72)
    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total - failed - errors - skipped
    print(f"  RESULTS: {passed}/{total} PASSED | {failed} FAILED | {errors} ERRORS | {skipped} SKIPPED")
    print("=" * 72)
