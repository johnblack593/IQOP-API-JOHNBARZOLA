import time

from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector
import types
from collections import deque

SUITE_NAME = "K_EdgeCases"

def run(api: IQ_Option, collector: ReportCollector) -> None:

    # K-01: buy_order con params inválidos — amount negativo
    start = time.time()
    try:
        check, msg = api.buy_order(instrument_type="crypto", instrument_id="BTCUSD", side="buy", amount=-1, leverage=10, type="market")
        assert check is False, "buy_order accepted negative amount"
        assert "INVALID_PARAMS" in str(msg), f"Expected INVALID_PARAMS for negative amount, got: {msg}"
        collector.record(TestResult(SUITE_NAME, "K-01: buy_order invalid amount", "PASSED", detail=str(msg), duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "K-01: buy_order invalid amount", "FAILED", detail=str(e), duration=time.time() - start))

    # K-02: buy_order con params inválidos — SL sin value
    start = time.time()
    try:
        check, msg = api.buy_order(instrument_type="crypto", instrument_id="BTCUSD", side="buy", amount=1, leverage=10, type="market", stop_lose_kind="percent", stop_lose_value=None)
        assert check is False, "buy_order accepted SL kind without value"
        assert "INVALID_PARAMS" in str(msg), f"Expected INVALID_PARAMS for SL without value, got: {msg}"
        collector.record(TestResult(SUITE_NAME, "K-02: buy_order missing SL value", "PASSED", detail=str(msg), duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "K-02: buy_order missing SL value", "FAILED", detail=str(e), duration=time.time() - start))

    # K-03: change_order con params inválidos — TP negativo
    start = time.time()
    try:
        check, msg = api.change_order(ID_Name="position_id", order_id=123, stop_lose_kind=None, stop_lose_value=None, take_profit_kind="percent", take_profit_value=-10, use_trail_stop=False, auto_margin_call=False)
        assert check is False, "change_order accepted negative TP value"
        assert "INVALID_PARAMS" in str(msg), f"Expected INVALID_PARAMS for negative TP, got: {msg}"
        collector.record(TestResult(SUITE_NAME, "K-03: change_order invalid TP", "PASSED", detail=str(msg), duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "K-03: change_order invalid TP", "FAILED", detail=str(e), duration=time.time() - start))

    # K-04: unsubscribe_live_deal
    start = time.time()
    try:
        # Just check existence
        assert hasattr(api, "unsubscribe_live_deal"), "unsubscribe_live_deal method is missing"
        assert hasattr(api, "unscribe_live_deal"), "unscribe_live_deal alias is missing"
        collector.record(TestResult(SUITE_NAME, "K-04: unsubscribe_live_deal rename", "PASSED", detail="Methods exist", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "K-04: unsubscribe_live_deal rename", "FAILED", detail=str(e), duration=time.time() - start))

    # K-05: get_blitz_instruments idempotencia
    start = time.time()
    try:
        blitz1 = api.get_blitz_instruments()
        blitz2 = api.get_blitz_instruments()
        assert blitz1 is blitz2, "get_blitz_instruments() did not return the identical dictionary on second call"
        collector.record(TestResult(SUITE_NAME, "K-05: get_blitz_instruments idempotency", "PASSED", detail="Returned identical dict mapping", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "K-05: get_blitz_instruments idempotency", "FAILED", detail=str(e), duration=time.time() - start))
