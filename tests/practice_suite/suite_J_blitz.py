import time
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "J_Blitz"


def run(api: IQ_Option, collector: ReportCollector) -> None:
    # Test J-01: Blitz catalog loaded
    start = time.time()
    blitz = {}
    try:
        # initialization-data may arrive slightly after connect() returns;
        # poll briefly to allow the WS handler to populate blitz_instruments
        for _ in range(10):
            blitz = api.get_blitz_instruments()
            if blitz:
                break
            time.sleep(0.5)
        assert isinstance(blitz, dict), f"Expected dict, got {type(blitz)}"
        assert len(blitz) > 0, "Blitz catalog is empty"
        collector.record(TestResult(SUITE_NAME, "J-01: Blitz catalog loaded", "PASSED",
                                    detail=f"{len(blitz)} instruments", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "J-01: Blitz catalog loaded", "FAILED",
                                    detail=str(e), duration=time.time() - start))
        # If catalog failed, skip remaining tests
        msg = "Catalog not loaded"
        collector.record(TestResult(SUITE_NAME, "J-02: Blitz asset has valid ID", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "J-03: Blitz expiration format", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "J-04: Blitz open_time availability", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "J-05: Buy blitz — CALL", "SKIPPED", detail=msg))
        return

    # Test J-02: Blitz asset has valid ID
    start = time.time()
    first_name = None
    first_data = None
    try:
        first_name = next(iter(blitz))
        first_data = blitz[first_name]
        assert "id" in first_data, f"Missing 'id' key in {first_name}"
        assert isinstance(first_data["id"], int), f"id is {type(first_data['id'])}, expected int"
        assert first_data["id"] > 0, f"id is {first_data['id']}, expected > 0"
        collector.record(TestResult(SUITE_NAME, "J-02: Blitz asset has valid ID", "PASSED",
                                    detail=f"{first_name} id={first_data['id']}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "J-02: Blitz asset has valid ID", "FAILED",
                                    detail=str(e), duration=time.time() - start))

    # Test J-03: Blitz expiration format
    start = time.time()
    try:
        assert first_data is not None, "No first_data from J-02"
        expirations = first_data.get("expirations", [])
        assert isinstance(expirations, list), f"expirations is {type(expirations)}, expected list"
        assert len(expirations) > 0, "expirations list is empty"
        # All expirations should be positive integers (seconds)
        for exp in expirations:
            assert isinstance(exp, (int, float)) and exp > 0, f"Invalid expiration: {exp}"
        collector.record(TestResult(SUITE_NAME, "J-03: Blitz expiration format", "PASSED",
                                    detail=f"{first_name} expirations={expirations}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "J-03: Blitz expiration format", "FAILED",
                                    detail=str(e), duration=time.time() - start))

    # Test J-04: Blitz open_time availability
    start = time.time()
    blitz_in_open_time = None
    open_blitz = {}
    try:
        open_blitz = {name: data for name, data in blitz.items() if data.get("open") is True}
        if len(open_blitz) > 0:
            blitz_in_open_time = next(iter(open_blitz))
            examples = list(open_blitz.keys())[:3]
            collector.record(TestResult(SUITE_NAME, "J-04: Blitz open_time availability", "PASSED",
                                        detail=f"{len(open_blitz)} open, e.g. {', '.join(examples)}",
                                        duration=time.time() - start))
        else:
            collector.record(TestResult(SUITE_NAME, "J-04: Blitz open_time availability", "SKIPPED",
                                        detail="SKIPPED_NO_MARKET — Blitz assets exist in catalog but none open",
                                        duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "J-04: Blitz open_time availability", "FAILED",
                                    detail=str(e), duration=time.time() - start))

    # Test J-05: Buy blitz - CALL (market-dependent)
    start = time.time()
    
    # Priority picking: known compatible binary-style assets
    BLITZ_PRIORITY = ["EURAUD-OTC", "EURUSD-OTC", "EURJPY-OTC", "LTCUSD-OTC", "BTCUSD-OTC"]
    target_asset = None
    for p_asset in BLITZ_PRIORITY:
        if p_asset in open_blitz:
            target_asset = p_asset
            break
    
    if not target_asset and blitz_in_open_time:
        target_asset = blitz_in_open_time

    if not target_asset:
        collector.record(TestResult(SUITE_NAME, "J-05: Buy blitz — CALL", "SKIPPED",
                                    detail="SKIPPED_NO_MARKET — No open blitz asset for trading",
                                    duration=time.time() - start))
        return

    try:
        # Use smallest expiration available
        asset_data = open_blitz[target_asset]
        exp = min(asset_data.get("expirations", [60]))

        # Wait for rate limiter to refill after J-01..J-04 API calls
        time.sleep(3)

        # Attempt buy — blitz assets use the same binary buy path
        # since they share active IDs with the binary/turbo ACTIVES table.
        check, order_id = api.buy(1, target_asset, "call", exp)
        if check is True and order_id is not None:
            collector.record(TestResult(SUITE_NAME, "J-05: Buy blitz — CALL", "PASSED",
                                        detail=f"Asset: {target_asset}, ID: {order_id}, exp: {exp}s",
                                        duration=time.time() - start))
        else:
            # Distinguish between rate limit and actual failure
            reason = str(order_id) if order_id else "no response"
            collector.record(TestResult(SUITE_NAME, "J-05: Buy blitz — CALL", "FAILED",
                                        detail=f"check={check}, reason={reason}, asset={target_asset}",
                                        duration=time.time() - start))
    except KeyError as e:
        collector.record(TestResult(SUITE_NAME, "J-05: Buy blitz — CALL", "FAILED",
                                    detail=f"Active not in OP_code.ACTIVES: {e}",
                                    duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "J-05: Buy blitz — CALL", "FAILED",
                                    detail=f"{type(e).__name__}: {e}",
                                    duration=time.time() - start))
