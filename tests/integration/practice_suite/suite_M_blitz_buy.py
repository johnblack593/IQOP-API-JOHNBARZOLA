"""Suite M — Blitz Buy Regression Guard.

Ensures blitz assets (binary-like OTC instruments with short expirations)
can be resolved in OP_code.ACTIVES and bought via api.buy().
Created after SPRINT-16 identified rate-limiter interference and asset compatibility issues.
"""

import time
import iqoptionapi.constants as OP_code
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "M_BlitzBuy"


def run(api: IQ_Option, collector: ReportCollector) -> None:
    # Load blitz catalog
    blitz = api.get_blitz_instruments()
    open_blitz = {n: d for n, d in blitz.items() if d.get("open") is True}

    if not open_blitz:
        msg = "SKIPPED_NO_MARKET — No open blitz assets"
        for test_name in [
            "M-01: buy() resolves blitz active_id",
            "M-02: buy() blitz CALL executes",
            "M-03: buy() blitz PUT executes",
        ]:
            collector.record(TestResult(SUITE_NAME, test_name, "SKIPPED", detail=msg))
        return

    # Priority picking: known compatible binary-style assets
    BLITZ_PRIORITY = ["EURAUD-OTC", "EURUSD-OTC", "EURJPY-OTC", "LTCUSD-OTC", "BTCUSD-OTC"]
    target_asset = None
    for p_asset in BLITZ_PRIORITY:
        if p_asset in open_blitz:
            target_asset = p_asset
            break
    
    if not target_asset:
        target_asset = next(iter(open_blitz))

    asset_data = open_blitz[target_asset]
    exp = min(asset_data.get("expirations", [60]))

    # ── M-01: buy() resolves blitz active_id ──
    start = time.time()
    try:
        active_id = OP_code.ACTIVES.get(target_asset)
        assert active_id is not None, f"'{target_asset}' not in OP_code.ACTIVES"
        assert isinstance(active_id, int) and active_id > 0, f"Invalid active_id={active_id}"
        collector.record(TestResult(
            SUITE_NAME, "M-01: buy() resolves blitz active_id", "PASSED",
            detail=f"{target_asset} → active_id={active_id}",
            duration=time.time() - start
        ))
    except Exception as e:
        collector.record(TestResult(
            SUITE_NAME, "M-01: buy() resolves blitz active_id", "FAILED",
            detail=str(e), duration=time.time() - start
        ))
        # If resolution fails, skip buy tests
        msg = f"Active ID not resolved: {e}"
        collector.record(TestResult(SUITE_NAME, "M-02: buy() blitz CALL executes", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "M-03: buy() blitz PUT executes", "SKIPPED", detail=msg))
        return

    # Wait for rate limiter
    time.sleep(3)

    # ── M-02: buy() blitz CALL executes ──
    start = time.time()
    try:
        check, order_id = api.buy(1, target_asset, "call", exp)
        assert check is True, f"buy() returned check=False, reason={order_id}"
        assert isinstance(order_id, int) and order_id > 0, f"Invalid order_id={order_id}"
        collector.record(TestResult(
            SUITE_NAME, "M-02: buy() blitz CALL executes", "PASSED",
            detail=f"ID: {order_id}, asset: {target_asset}, exp: {exp}s",
            duration=time.time() - start
        ))
    except Exception as e:
        collector.record(TestResult(
            SUITE_NAME, "M-02: buy() blitz CALL executes", "FAILED",
            detail=str(e), duration=time.time() - start
        ))

    # Wait for rate limiter
    time.sleep(3)

    # ── M-03: buy() blitz PUT executes ──
    start = time.time()
    try:
        check, order_id = api.buy(1, target_asset, "put", exp)
        assert check is True, f"buy() returned check=False, reason={order_id}"
        assert isinstance(order_id, int) and order_id > 0, f"Invalid order_id={order_id}"
        collector.record(TestResult(
            SUITE_NAME, "M-03: buy() blitz PUT executes", "PASSED",
            detail=f"ID: {order_id}, asset: {target_asset}, exp: {exp}s",
            duration=time.time() - start
        ))
    except Exception as e:
        collector.record(TestResult(
            SUITE_NAME, "M-03: buy() blitz PUT executes", "FAILED",
            detail=str(e), duration=time.time() - start
        ))
