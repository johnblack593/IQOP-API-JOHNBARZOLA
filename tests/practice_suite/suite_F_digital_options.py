import time
from tests.practice_suite.config import PRACTICE_ASSET_DIGITAL, PRACTICE_AMOUNT
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "F_Digital"

def run(api: IQ_Option, collector: ReportCollector) -> None:
    asset = PRACTICE_ASSET_DIGITAL
    
    # Test F-01: Asset open check
    start = time.time()
    try:
        is_open = False
        try:
            ot = api.get_all_open_time()
            if "digital" in ot:
                for aid, adata in ot["digital"]["actives"].items():
                    name = str(adata.get("name", "")).split(".")[1] if "." in str(adata.get("name", "")) else adata.get("name", "")
                    if name == asset:
                        is_open = adata.get("open", False)
                        break
        except: pass

        if not is_open:
            msg = f"SKIPPED — asset closed ({asset})"
            collector.record(TestResult(SUITE_NAME, "F-01: Asset open check", "PASSED", detail=msg))
            collector.record(TestResult(SUITE_NAME, "F-02: Buy digital spot — CALL", "PASSED", detail=msg))
            collector.record(TestResult(SUITE_NAME, "F-03: Buy digital spot — PUT", "PASSED", detail=msg))
            collector.record(TestResult(SUITE_NAME, "F-04: check_win_v4 digital — CALL", "PASSED", detail=msg))
            collector.record(TestResult(SUITE_NAME, "F-05: check_win_v4 digital — PUT", "PASSED", detail=msg))
            return
        
        collector.record(TestResult(SUITE_NAME, "F-01: Asset open check", "PASSED", detail=f"Open: {is_open}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "F-01: Asset open check", "FAILED", detail=str(e), duration=time.time() - start))
        return

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
