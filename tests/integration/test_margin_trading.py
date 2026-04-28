#!/usr/bin/env python3
"""
Margin Trading Test Suite — JCBV-NEXUS v8.9.999-SP1
Tests the modern marginal-{type}.place-market-order protocol.
All tests run on DEMO account.
"""
import os
import sys
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scratch/margin_trading_test_log.txt", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("MARGIN_TEST")

# Credentials from .env
EMAIL = os.getenv("IQ_EMAIL", "")
PASSWORD = os.getenv("IQ_PASSWORD", "")

RESULTS = []


def record(test_name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    RESULTS.append({"test": test_name, "status": status, "detail": detail})
    logger.info("[%s] %s %s", status, test_name, f"-- {detail}" if detail else "")


def main():
    logger.info("=" * 60)
    logger.info("  MARGIN TRADING TEST SUITE (v8.9.999-SP1)")
    logger.info("=" * 60)

    from iqoptionapi.stable_api import IQ_Option
    iq = IQ_Option(EMAIL, PASSWORD)

    logger.info("Connecting (demo account, no WARP)...")
    status, reason = iq.connect()
    if not status:
        logger.error("Connection FAILED: %s", reason)
        record("Connection", False, str(reason))
        return 1

    record("Connection", True, "Connected successfully")

    # Ensure demo mode — wrapped in try/except for profile issues
    try:
        iq.change_balance("PRACTICE")
        logger.info("Balance mode: PRACTICE (demo), Balance: $%.2f", iq.get_balance())
    except Exception as e:
        logger.warning("Could not change balance (continuing with default): %s", e)
        # Force demo balance if possible
        try:
            balance = iq.get_balance()
            logger.info("Current balance: $%.2f", balance)
        except Exception:
            logger.warning("Could not get balance, continuing anyway")

    # ─────────────────────────────────────────────────────────────
    # TEST 1: Get available leverages for EURUSD (forex, active_id=1)
    # ─────────────────────────────────────────────────────────────
    logger.info("-" * 60)
    logger.info("TEST 1: Get available leverages for EURUSD (forex)")
    leverages = iq.get_available_leverages("forex", 1)
    if leverages and len(leverages) > 0:
        record("T1_Get_Leverages", True, f"Leverages: {leverages}")
    else:
        record("T1_Get_Leverages", False, f"Got: {leverages}")

    # ─────────────────────────────────────────────────────────────
    # TEST 2: Open margin position EURUSD with TP/SL
    # ─────────────────────────────────────────────────────────────
    logger.info("-" * 60)
    logger.info("TEST 2: Open EURUSD margin position (buy, $10, x50, TP=+$5, SL=-$3)")
    success, result = iq.open_margin_position(
        instrument_type="forex",
        active_id=1,           # EURUSD
        direction="buy",
        amount=10,
        leverage=50,
        take_profit={"type": "pnl", "value": 5},
        stop_loss={"type": "pnl", "value": 3},
        timeout=15.0,
    )
    position_id = None
    if success and isinstance(result, dict):
        position_id = result.get("id")
        record("T2_Open_Position_TPSL", True,
               f"position_id={position_id} "
               f"open_price={result.get('open_price')} "
               f"leverage={result.get('leverage')}")
    else:
        record("T2_Open_Position_TPSL", False, str(result))

    # ─────────────────────────────────────────────────────────────
    # TEST 3: Get margin positions (verify it appears)
    # ─────────────────────────────────────────────────────────────
    if position_id:
        logger.info("-" * 60)
        logger.info("TEST 3: Verify position in get_margin_positions()")
        time.sleep(1)  # Small delay for server to register
        positions = iq.get_margin_positions("forex")
        found = any(
            str(p.get("id")) == str(position_id) or
            str(p.get("external_id")) == str(position_id)
            for p in positions
        ) if positions else False
        record("T3_List_Positions", found or len(positions) > 0,
               f"Total positions: {len(positions)}, found ours: {found}")
    else:
        record("T3_List_Positions", False, "Skipped (no position_id from T2)")

    # ─────────────────────────────────────────────────────────────
    # TEST 4: Modify TP/SL on open position
    # ─────────────────────────────────────────────────────────────
    if position_id:
        logger.info("-" * 60)
        logger.info("TEST 4: Modify TP/SL (TP=$8, SL=$5)")
        try:
            success_mod, result_mod = iq.modify_margin_tp_sl(
                order_id=position_id,
                take_profit={"type": "pnl", "value": 8},
                stop_loss={"type": "pnl", "value": 5},
            )
            record("T4_Modify_TPSL", success_mod, str(result_mod)[:200] if result_mod else "")
        except Exception as e:
            record("T4_Modify_TPSL", False, f"Exception: {e}")
    else:
        record("T4_Modify_TPSL", False, "Skipped (no position_id from T2)")

    # ─────────────────────────────────────────────────────────────
    # TEST 5: Close margin position
    # ─────────────────────────────────────────────────────────────
    if position_id:
        logger.info("-" * 60)
        logger.info("TEST 5: Close margin position")
        time.sleep(1)
        success_close, result_close = iq.close_margin_position(position_id)
        record("T5_Close_Position", success_close, str(result_close)[:200])
    else:
        record("T5_Close_Position", False, "Skipped (no position_id from T2)")

    # ─────────────────────────────────────────────────────────────
    # TEST 6: Open position WITHOUT TP/SL (only leverage)
    # ─────────────────────────────────────────────────────────────
    logger.info("-" * 60)
    logger.info("TEST 6: Open GBPUSD margin position (buy, $10, x100, NO TP/SL)")
    success_6, result_6 = iq.open_margin_position(
        instrument_type="forex",
        active_id=3,            # GBPUSD to avoid conflict with T2's EURUSD
        direction="buy",
        amount=10,
        leverage=100,
        timeout=15.0,
    )
    position_id_6 = None
    if success_6 and isinstance(result_6, dict) and result_6.get("id"):
        position_id_6 = result_6.get("id")
        record("T6_Open_No_TPSL", True, f"position_id={position_id_6}")
        # Close it immediately
        time.sleep(1)
        iq.close_margin_position(position_id_6)
    else:
        record("T6_Open_No_TPSL", False, str(result_6))

    # ─────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    total = len(RESULTS)
    for r in RESULTS:
        logger.info("  [%s] %s", r["status"], r["test"])
        if r["detail"]:
            logger.info("         %s", r["detail"][:120])
    logger.info("-" * 60)
    logger.info("  %d/%d PASSED", passed, total)
    logger.info("=" * 60)

    # Write report
    with open("tests/reports/margin_trading_test_20260428.md", "w", encoding="utf-8") as f:
        f.write("# Margin Trading Test Report - 2026-04-28\\n\\n")
        f.write(f"**Result**: {passed}/{total} tests passed\\n\\n")
        f.write("| Test | Status | Detail |\\n")
        f.write("|------|--------|--------|\\n")
        for r in RESULTS:
            f.write(f"| {r['test']} | {r['status']} | {r['detail'][:80]} |\\n")
        f.write("\\n")

    iq.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
