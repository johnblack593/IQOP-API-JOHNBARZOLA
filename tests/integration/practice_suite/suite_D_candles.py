import time
from tests.practice_suite.config import get_available_binary_asset
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "D_Candles"

def run(api: IQ_Option, collector: ReportCollector) -> None:
    asset = get_available_binary_asset(api, "binary")

    if not asset:
        msg = "SKIPPED_NO_MARKET \u2014 No binary/turbo asset available"
        collector.record(TestResult(SUITE_NAME, "D-01: Get candles 60s", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "D-02: Get candles 300s", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "D-03: Get candles 3600s", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "D-04: Candle data integrity", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "D-05: Realtime subscription", "SKIPPED", detail=msg))
        return

    # Test D-01: Get candles 60s
    start = time.time()
    candles_60 = None
    try:
        candles_60 = api.get_candles(asset, 60, 10, time.time())
        assert isinstance(candles_60, list), "Result is not a list"
        assert len(candles_60) > 0, "No candles returned"
        for key in ["open", "close", "min", "max", "volume"]:
            assert key in candles_60[0], f"Missing key {key}"
        collector.record(TestResult(SUITE_NAME, "D-01: Get candles 60s", "PASSED", detail=f"Count: {len(candles_60)}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "D-01: Get candles 60s", "FAILED", detail=str(e), duration=time.time() - start))

    # Test D-02: Get candles 300s
    start = time.time()
    try:
        c = api.get_candles(asset, 300, 10, time.time())
        assert isinstance(c, list) and len(c) > 0, "Failed to get 300s candles"
        collector.record(TestResult(SUITE_NAME, "D-02: Get candles 300s", "PASSED", detail=f"Count: {len(c)}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "D-02: Get candles 300s", "FAILED", detail=str(e), duration=time.time() - start))

    # Test D-03: Get candles 3600s
    start = time.time()
    try:
        c = api.get_candles(asset, 3600, 10, time.time())
        assert isinstance(c, list) and len(c) > 0, "Failed to get 3600s candles"
        collector.record(TestResult(SUITE_NAME, "D-03: Get candles 3600s", "PASSED", detail=f"Count: {len(c)}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "D-03: Get candles 3600s", "FAILED", detail=str(e), duration=time.time() - start))

    # Test D-04: Candle data integrity
    start = time.time()
    try:
        assert candles_60 is not None, "D-01 failed, cannot test integrity"
        passed_count = 0
        for rc in candles_60:
            c_open, c_close = rc["open"], rc["close"]
            c_min, c_max = rc["min"], rc["max"]
            assert c_open > 0 and c_close > 0, "Zero or negative OHLC"
            assert c_min <= c_open and c_min <= c_close, f"min={c_min} is not <= open={c_open} and close={c_close}"
            assert c_max >= c_open and c_max >= c_close, f"max={c_max} is not >= open={c_open} and close={c_close}"
            passed_count += 1
            
        collector.record(TestResult(SUITE_NAME, "D-04: Candle data integrity", "PASSED", detail=f"{passed_count} verified", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "D-04: Candle data integrity", "FAILED", detail=str(e), duration=time.time() - start))

    # Test D-05: Realtime subscription
    start = time.time()
    try:
        api.start_candles_stream(asset, 60, 1)
        time.sleep(3)
        rt_candles = api.get_realtime_candles(asset, 60)
        api.stop_candles_stream(asset, 60)

        assert rt_candles is not None, "get_realtime_candles returned None"
        assert isinstance(rt_candles, dict), "realtime candles should be a dict"
        collector.record(TestResult(SUITE_NAME, "D-05: Realtime subscription", "PASSED", detail=f"Received streaming blocks: {len(rt_candles) if rt_candles else 0}", duration=time.time() - start))
    except Exception as e:
        # cleanup just in case
        try: api.stop_candles_stream(asset, 60)
        except: pass
        collector.record(TestResult(SUITE_NAME, "D-05: Realtime subscription", "FAILED", detail=str(e), duration=time.time() - start))

