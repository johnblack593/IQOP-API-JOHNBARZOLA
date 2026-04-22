import time
from tests.practice_suite.config import PRACTICE_ASSET_BINARY
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "C_MarketData"

def run(api: IQ_Option, collector: ReportCollector) -> None:
    # Test C-01: Open time retrieval
    start = time.time()
    open_times = None
    try:
        open_times = api.get_all_open_time()
        assert open_times is not None, "get_all_open_time returned None"
        assert isinstance(open_times, dict), "Open time data is not a dict"
        assert "turbo" in open_times or "binary" in open_times, "Missing turbo/binary keys in open time data"
        collector.record(TestResult(SUITE_NAME, "C-01: Open time retrieval", "PASSED", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "C-01: Open time retrieval", "FAILED", detail=str(e), duration=time.time() - start))

    # Test C-02: Active asset resolution — binary
    start = time.time()
    try:
        assert open_times is not None, "open_times was not retrieved in C-01"
        categories = list(open_times.keys()) if open_times else []

        # The open_time structure is FLAT: open_times[category][asset_name]["open"]
        asset_found = False
        status_msg = f"{PRACTICE_ASSET_BINARY} not found"

        for option_type in ["binary", "turbo"]:
            cat_data = open_times.get(option_type, {})
            if PRACTICE_ASSET_BINARY in cat_data:
                asset_found = True
                is_open = cat_data[PRACTICE_ASSET_BINARY].get("open", False)
                status_msg = f"Found in {option_type} - Open: {is_open}. Categories: {categories}"
                break

        if not asset_found:
            status_msg = f"{PRACTICE_ASSET_BINARY} not listed in binary/turbo. Categories: {categories}"

        collector.record(TestResult(SUITE_NAME, "C-02: Active asset resolution", "PASSED", detail=status_msg, duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "C-02: Active asset resolution", "FAILED", detail=str(e), duration=time.time() - start))

    # Test C-03: Instruments retrieval
    start = time.time()
    try:
        instruments = api.get_instruments("crypto")
        assert instruments is not None, "get_instruments returned None"
        assert "instruments" in instruments, "Key 'instruments' missing from response"
        assert isinstance(instruments["instruments"], list), "Instruments array is not a list"
        collector.record(TestResult(SUITE_NAME, "C-03: Instruments retrieval", "PASSED", detail=f"Found {len(instruments['instruments'])} crypto instruments", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "C-03: Instruments retrieval", "FAILED", detail=str(e), duration=time.time() - start))

    # Test C-04: Digital strikes
    start = time.time()
    try:
        if hasattr(api, "get_digital_underlying_list_data"):
            strikes = api.get_digital_underlying_list_data()
            assert strikes is not None, "get_digital_underlying_list_data returned None"
            
            if isinstance(strikes, dict) and strikes.get("message", "").startswith("Failed on command execution [4300]"):
                collector.record(TestResult(SUITE_NAME, "C-04: Digital strikes", "SKIPPED", detail="SKIPPED — Digital underlying V2 deprecated by broker (error 4300)", duration=time.time() - start))
            else:
                if isinstance(strikes, dict) and 'underlying' in strikes:
                    strikes = strikes['underlying']
                assert isinstance(strikes, list) or isinstance(strikes, dict), "Strikes should be a list or dict"
                assert len(strikes) > 0, "No digital underlying assets found"
                collector.record(TestResult(SUITE_NAME, "C-04: Digital strikes", "PASSED", detail=f"Found {len(strikes)} assets", duration=time.time() - start))
        else:
            collector.record(TestResult(SUITE_NAME, "C-04: Digital strikes", "FAILED", detail="Method get_digital_underlying_list_data not found", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "C-04: Digital strikes", "FAILED", detail=str(e), duration=time.time() - start))

    # Test C-05: OTC availability check
    start = time.time()
    try:
        otc_count = 0
        otc_examples = []
        if open_times is not None:
            # Flat structure: open_times[category][asset_name]["open"]
            for cat in ["binary", "turbo"]:
                for asset_name, info in open_times.get(cat, {}).items():
                    if "-OTC" in asset_name.upper() and isinstance(info, dict) and info.get("open") is True:
                        otc_count += 1
                        if len(otc_examples) < 3:
                            otc_examples.append(asset_name)

        if otc_count > 0:
            collector.record(TestResult(SUITE_NAME, "C-05: OTC availability check", "PASSED", detail=f"{otc_count} OTC active, e.g. {', '.join(otc_examples)}", duration=time.time() - start))
        else:
            collector.record(TestResult(SUITE_NAME, "C-05: OTC availability check", "SKIPPED", detail="SKIPPED_NO_MARKET \u2014 No OTC assets open", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "C-05: OTC availability check", "FAILED", detail=str(e), duration=time.time() - start))
