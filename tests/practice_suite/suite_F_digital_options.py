import time
from tests.practice_suite.config import PRACTICE_AMOUNT, get_available_digital_asset
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "F_Digital"

def run(api: IQ_Option, collector: ReportCollector) -> None:
    asset = get_available_digital_asset(api)
    
    if not asset:
        msg = "SKIPPED_NO_MARKET \u2014 No digital asset available"
        collector.record(TestResult(SUITE_NAME, "F-01: Asset open check", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "F-02: Buy digital spot \u2014 CALL", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "F-03: Buy digital spot \u2014 PUT", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "F-04: check_win_v4 digital \u2014 CALL", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "F-05: check_win_v4 digital \u2014 PUT", "SKIPPED", detail=msg))
        return
        
    start = time.time()
    collector.record(TestResult(SUITE_NAME, "F-01: Asset open check", "PASSED", detail=f"Open: {asset}", duration=time.time() - start))

    # Let TokenBucket refill
    time.sleep(2)

    # Test F-02: Buy digital spot — CALL
    start = time.time()
    f02_order_id = None
    try:
        check, order_id = api.buy_digital_spot_v2(asset, PRACTICE_AMOUNT, "call", 1)
        assert check, f"Digital buy failed: {order_id}"
        assert order_id is not None, "Order ID is None"
        f02_order_id = order_id
        collector.record(TestResult(SUITE_NAME, "F-02: Buy digital spot — CALL", "PASSED", detail=f"ID: {order_id}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "F-02: Buy digital spot — CALL", "FAILED", detail=str(e), duration=time.time() - start))

    time.sleep(2)

    # Test F-03: Buy digital spot — PUT
    start = time.time()
    f03_order_id = None
    try:
        check, order_id = api.buy_digital_spot_v2(asset, PRACTICE_AMOUNT, "put", 1)
        assert check, f"Digital buy failed: {order_id}"
        assert order_id is not None, "Order ID is None"
        f03_order_id = order_id
        collector.record(TestResult(SUITE_NAME, "F-03: Buy digital spot — PUT", "PASSED", detail=f"ID: {order_id}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "F-03: Buy digital spot — PUT", "FAILED", detail=str(e), duration=time.time() - start))

    # Wait for expirations (digital orders require waiting)
    time.sleep(2)

    # Test F-04: check_win_v4 digital — CALL
    start = time.time()
    try:
        if f02_order_id is None:
            raise ValueError("f02_order_id is None")
        result = api.check_win_v4(f02_order_id)
        assert result is not None, "check_win_v4 returned None"
        collector.record(TestResult(SUITE_NAME, "F-04: check_win_v4 digital — CALL", "PASSED", detail=f"Outcome: {result}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "F-04: check_win_v4 digital — CALL", "FAILED", detail=str(e), duration=time.time() - start))

    # Test F-05: check_win_v4 digital — PUT
    start = time.time()
    try:
        if f03_order_id is None:
            raise ValueError("f03_order_id is None")
        result = api.check_win_v4(f03_order_id)
        assert result is not None, "check_win_v4 returned None"
        collector.record(TestResult(SUITE_NAME, "F-05: check_win_v4 digital — PUT", "PASSED", detail=f"Outcome: {result}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "F-05: check_win_v4 digital — PUT", "FAILED", detail=str(e), duration=time.time() - start))
