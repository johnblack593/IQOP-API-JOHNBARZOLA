import sys
import time
import certifi
import iqoptionapi
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.ratelimit import TokenBucket, RateLimitExceededError
from iqoptionapi.http.session import get_shared_session
from iqoptionapi.reconnect import ReconnectManager
from iqoptionapi.idempotency import IdempotencyRegistry

from examples.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "A_Infrastructure"

def run(api: IQ_Option, collector: ReportCollector) -> None:
    # Test A-01: Version check
    start = time.time()
    try:
        ver = iqoptionapi.__version__
        parts = ver.split('.')
        assert len(parts) >= 3, "Version does not match X.Y.Z pattern"
        assert "version_control" not in sys.modules, "version_control module is unexpectedly loaded"
        collector.record(TestResult(SUITE_NAME, "A-01: Version check", True, detail=f"Version: {ver}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "A-01: Version check", False, detail=str(e), duration=time.time() - start))

    # Test A-02: Rate limiter token availability
    start = time.time()
    try:
        bucket = TokenBucket(capacity=3.0, refill_rate=0.5, block=False)
        bucket.consume()
        bucket.consume()
        bucket.consume()
        try:
            bucket.consume()
            assert False, "4th consume() did not raise RateLimitExceededError"
        except RateLimitExceededError:
            pass # Expected state
        collector.record(TestResult(SUITE_NAME, "A-02: Rate limiter token avail", True, duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "A-02: Rate limiter token avail", False, detail=str(e), duration=time.time() - start))

    # Test A-03: TLS session singleton
    start = time.time()
    try:
        s1 = get_shared_session()
        s2 = get_shared_session()
        assert s1 is s2, "get_shared_session did not return the identical singleton object"
        assert s1.verify == certifi.where(), "Session verify is not mapped to certifi.where()"
        collector.record(TestResult(SUITE_NAME, "A-03: TLS session singleton", True, duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "A-03: TLS session singleton", False, detail=str(e), duration=time.time() - start))

    # Test A-04: Reconnect manager reset
    start = time.time()
    try:
        # Mocking time.sleep for the wait instance so it doesn't actually stall the suite execution
        original_sleep = time.sleep
        def dummy_sleep(secs): pass
        time.sleep = dummy_sleep
        
        manager = ReconnectManager(max_attempts=5, cap=10, base=2)
        try:
            manager.wait()
            manager.wait()
        finally:
            time.sleep = original_sleep # Always restore

        assert manager._attempt == 2, f"Expected 2 attempts, got {manager._attempt}"
        manager.reset()
        assert manager._attempt == 0, "Attempts did not reset to 0"
        collector.record(TestResult(SUITE_NAME, "A-04: Reconnect manager reset", True, duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "A-04: Reconnect manager reset", False, detail=str(e), duration=time.time() - start))

    # Test A-05: Idempotency registry lifecycle
    start = time.time()
    try:
        registry = IdempotencyRegistry()
        req_id = registry.register()
        
        record = registry._store[req_id]
        
        assert record["state"] == registry.PENDING, "State is not PENDING"
        
        registry.confirm(req_id, "fake_order_123")
        assert record["state"] == registry.CONFIRMED, "State is not CONFIRMED"
        assert registry.get_order_id(req_id) == "fake_order_123", "Stored order ID does not match"

        collector.record(TestResult(SUITE_NAME, "A-05: Idempotency lifecycle", True, duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "A-05: Idempotency lifecycle", False, detail=str(e), duration=time.time() - start))
