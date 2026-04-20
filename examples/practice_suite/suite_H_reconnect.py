import time
from iqoptionapi.stable_api import IQ_Option
from examples.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "H_Reconnect"

def run(api: IQ_Option, collector: ReportCollector) -> None:
    # Test H-01: Forced WebSocket disconnect
    start = time.time()
    try:
        api.api.close()
        time.sleep(2)
        assert api.api.websocket_client is not None, "Websocket client object was destroyed"
        collector.record(TestResult(SUITE_NAME, "H-01: Forced WS disconnect", True, duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "H-01: Forced WS disconnect", False, detail=str(e), duration=time.time() - start))

    # Test H-02: Reconnect and re-authenticate
    start = time.time()
    try:
        from examples.practice_suite.config import IQ_EMAIL, IQ_PASSWORD
        api = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        import examples.practice_suite.config as config
        config.api_instance = api # Save for next suites

        check, msg = api.connect()
        assert check, f"Reconnect failed: {msg}"
        
        api.change_balance("PRACTICE")
        bal = api.get_balance()
        assert bal is not None and bal >= 0, "Balance retrieval failed after reconnect"
        collector.record(TestResult(SUITE_NAME, "H-02: Reconnect and auth", True, detail=f"Balance: {bal}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "H-02: Reconnect and auth", False, detail=str(e), duration=time.time() - start))

    # Test H-03: Backoff manager reset after successful connect
    start = time.time()
    try:
        assert hasattr(api, "_reconnect_manager"), "Reconnect manager not found"
        assert api._reconnect_manager._attempt == 0, f"Manager attempts are {api._reconnect_manager._attempt}, not 0"
        collector.record(TestResult(SUITE_NAME, "H-03: Backoff reset", True, duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "H-03: Backoff reset", False, detail=str(e), duration=time.time() - start))

    # Test H-04: Post-reconnect balance type
    start = time.time()
    try:
        mode = "UNKNOWN"
        if hasattr(api, "get_balance_mode"):
            mode = api.get_balance_mode()
        elif hasattr(api, "get_balance_type"):
            mode = api.get_balance_type()
            
        assert mode == "PRACTICE", f"Balance mode is not PRACTICE: {mode}"
        collector.record(TestResult(SUITE_NAME, "H-04: Post-reconnect mode", True, detail=f"Mode: {mode}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "H-04: Post-reconnect mode", False, detail=str(e), duration=time.time() - start))
