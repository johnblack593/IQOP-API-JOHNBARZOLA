"""
Suite L: HTTP/Init-Data Instrument Fallback Verification
Sprint-14: Validates that the init-data fallback for get_instruments()
works correctly when WS returns empty instrument lists.
"""
import time

import iqoptionapi.core.constants as OP_code
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "L_HTTPInstruments"


def run(api: IQ_Option, collector: ReportCollector) -> None:

    # ──────────────────────────────────────────────────────────────
    # L-01: Session has valid auth cookies
    # ──────────────────────────────────────────────────────────────
    start = time.time()
    try:
        from iqoptionapi.http.session import get_shared_session
        session = get_shared_session()
        cookie_names = [c.name for c in session.cookies]
        has_ssid = any("ssid" in n.lower() for n in cookie_names)
        assert has_ssid, f"No SSID cookie found. Cookies: {cookie_names}"
        collector.record(TestResult(
            SUITE_NAME, "L-01: Session has auth cookies",
            "PASSED", detail=f"cookies={cookie_names}",
            duration=time.time() - start
        ))
    except Exception as e:
        collector.record(TestResult(
            SUITE_NAME, "L-01: Session has auth cookies",
            "FAILED", detail=str(e), duration=time.time() - start
        ))

    # ──────────────────────────────────────────────────────────────
    # L-02: Fallback returns data for "forex"
    # ──────────────────────────────────────────────────────────────
    start = time.time()
    try:
        result = api.get_instruments("forex")
        instruments = result.get("instruments", [])
        count = len(instruments)
        assert count > 0, "get_instruments('forex') returned 0 instruments"
        sample = [ins.get("id", "?") for ins in instruments[:5]]
        collector.record(TestResult(
            SUITE_NAME, "L-02: forex instruments",
            "PASSED", detail=f"{count} instruments: {sample}",
            duration=time.time() - start
        ))
    except Exception as e:
        collector.record(TestResult(
            SUITE_NAME, "L-02: forex instruments",
            "FAILED", detail=str(e), duration=time.time() - start
        ))

    # ──────────────────────────────────────────────────────────────
    # L-03: Fallback returns data for "cfd"
    # ──────────────────────────────────────────────────────────────
    start = time.time()
    try:
        result = api.get_instruments("cfd")
        instruments = result.get("instruments", [])
        count = len(instruments)
        assert count > 0, "get_instruments('cfd') returned 0 instruments"
        sample = [ins.get("id", "?") for ins in instruments[:5]]
        collector.record(TestResult(
            SUITE_NAME, "L-03: cfd instruments",
            "PASSED", detail=f"{count} instruments: {sample}",
            duration=time.time() - start
        ))
    except Exception as e:
        collector.record(TestResult(
            SUITE_NAME, "L-03: cfd instruments",
            "FAILED", detail=str(e), duration=time.time() - start
        ))

    # ──────────────────────────────────────────────────────────────
    # L-04: Instruments load into ACTIVES
    # ──────────────────────────────────────────────────────────────
    start = time.time()
    try:
        # Force re-update ACTIVES with fallback data
        api.update_ACTIVES_OPCODE()
        # Check that we have forex pairs in ACTIVES
        forex_keys = [k for k in OP_code.ACTIVES.keys()
                      if k in ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
                               "EURJPY", "GBPJPY", "USDCHF", "NZDUSD")]
        assert len(forex_keys) > 0, \
            f"No forex major found in ACTIVES. Total keys: {len(OP_code.ACTIVES)}"
        collector.record(TestResult(
            SUITE_NAME, "L-04: instruments in ACTIVES",
            "PASSED", detail=f"forex majors found: {forex_keys}",
            duration=time.time() - start
        ))
    except Exception as e:
        collector.record(TestResult(
            SUITE_NAME, "L-04: instruments in ACTIVES",
            "FAILED", detail=str(e), duration=time.time() - start
        ))

    # ──────────────────────────────────────────────────────────────
    # L-05: get_all_open_time() includes forex assets
    # ──────────────────────────────────────────────────────────────
    start = time.time()
    try:
        open_times = api.get_all_open_time()
        forex_data = open_times.get("forex", {})
        total_forex = len(forex_data)
        open_forex = [name for name, info in forex_data.items()
                      if isinstance(info, dict) and info.get("open") is True]
        assert total_forex > 0, \
            f"forex category has 0 assets in open_times"
        detail = f"{total_forex} total, {len(open_forex)} open"
        if open_forex:
            detail += f" | sample: {open_forex[:5]}"
        collector.record(TestResult(
            SUITE_NAME, "L-05: forex in open_times",
            "PASSED", detail=detail,
            duration=time.time() - start
        ))
    except Exception as e:
        collector.record(TestResult(
            SUITE_NAME, "L-05: forex in open_times",
            "FAILED", detail=str(e), duration=time.time() - start
        ))

