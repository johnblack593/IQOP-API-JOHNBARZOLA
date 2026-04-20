import time
from tests.practice_suite.config import PRACTICE_AMOUNT
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector
import logging

logger = logging.getLogger(__name__)

SUITE_NAME = "G_CFD"

def get_available_cfd_asset(api):
    CFD_FOREX_PRIORITY = [
        "EURUSD", "GBPUSD", "AUDUSD", "USDJPY",
        "USDCAD", "USDCHF", "NZDUSD", "EURJPY",
    ]
    open_times = api.get_all_open_time()

    for category in ["forex", "cfd"]:
        cat_data = open_times.get(category, {})
        for asset in CFD_FOREX_PRIORITY:
            if cat_data.get(asset, {}).get("open") is True:
                return category, asset

    for category in ["forex", "cfd"]:
        cat_data = open_times.get(category, {})
        for asset_name, info in cat_data.items():
            if info.get("open") is True:
                return category, asset_name

    return None, None

def run(api: IQ_Option, collector: ReportCollector) -> None:
    category, asset = get_available_cfd_asset(api)
    
    if not asset:
        msg = "SKIPPED_NO_MARKET \u2014 No CFD assets available at execution time (weekend/holiday)"
        collector.record(TestResult(SUITE_NAME, "G-01: Asset open check", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "G-02: Buy CFD order \u2014 CALL", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "G-03: Get open position", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "G-04: Modify SL/TP", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "G-05: Close position manually", "SKIPPED", detail=msg))
        collector.record(TestResult(SUITE_NAME, "G-06: Buy order \u2014 PUT side", "SKIPPED", detail=msg))
        return

    # Track open positions for finally cleanup
    open_positions = []

    try:
        # Test G-01: Asset open check
        start = time.time()
        try:
            collector.record(TestResult(SUITE_NAME, "G-01: Asset open check", "PASSED", detail=f"Open: {asset}", duration=time.time() - start))
        except Exception as e:
            collector.record(TestResult(SUITE_NAME, "G-01: Asset open check", "FAILED", detail=str(e), duration=time.time() - start))

        time.sleep(1)

        # Test G-02: Buy CFD order — CALL with SL and TP
        start = time.time()
        g02_order_id = None
        try:
            check, order_id = api.buy_order(
                instrument_type=category,
                instrument_id=asset,
                side="buy", # "buy" / "call"
                amount=PRACTICE_AMOUNT,
                leverage=1, # Default safe leverage
                type="market",
                limit_price=None,
                stop_price=None,
                stop_lose_kind="percent",
                stop_lose_value=5.0,
                take_profit_kind="percent",
                take_profit_value=10.0
            )
            assert check, f"CFD buy order failed. check is False."
            assert order_id is not None, "Order ID is None"
            g02_order_id = order_id
            
            # Extract position_id to add to cleanup tracking
            time.sleep(1)
            o_check, o_data = api.get_order(g02_order_id)
            if o_check and isinstance(o_data, dict):
                pos_id = o_data.get("position_id", g02_order_id)
                open_positions.append(pos_id)
            else:
                open_positions.append(g02_order_id) # fallback
                
            collector.record(TestResult(SUITE_NAME, "G-02: Buy CFD order \u2014 CALL", "PASSED", detail=f"ID: {g02_order_id}", duration=time.time() - start))
        except Exception as e:
            collector.record(TestResult(SUITE_NAME, "G-02: Buy CFD order \u2014 CALL", "FAILED", detail=str(e), duration=time.time() - start))

        time.sleep(2)

        # Test G-03: Get open position
        start = time.time()
        try:
            if g02_order_id is None:
                raise ValueError("g02_order_id is None")
            check, order_data = api.get_order(g02_order_id)
            assert check, "Failed to get order data"
            assert order_data is not None, "Order data is None"
            status = order_data.get("status", "unknown")
            collector.record(TestResult(SUITE_NAME, "G-03: Get open position", "PASSED", detail=f"Status: {status}", duration=time.time() - start))
        except Exception as e:
            collector.record(TestResult(SUITE_NAME, "G-03: Get open position", "FAILED", detail=str(e), duration=time.time() - start))

        # Test G-04: Modify SL/TP on open position
        start = time.time()
        try:
            if g02_order_id is None:
                raise ValueError("g02_order_id is None")
            # For forex/CFD, position_id is usually tracked
            local_pos_id = open_positions[0] if open_positions else g02_order_id
            
            # API expects stop_lose_kind, stop_lose_value, take_profit_kind, take_profit_value
            api.change_order(
                ID_Name="position_id", 
                order_id=local_pos_id, 
                stop_lose_kind="percent", 
                stop_lose_value=3.0, 
                take_profit_kind="percent", 
                take_profit_value=8.0
            )
            collector.record(TestResult(SUITE_NAME, "G-04: Modify SL/TP", "PASSED", detail="SL/TP changed to 3%/8%", duration=time.time() - start))
        except Exception as e:
            collector.record(TestResult(SUITE_NAME, "G-04: Modify SL/TP", "FAILED", detail=str(e), duration=time.time() - start))

        # Test G-05: Close open position manually
        start = time.time()
        try:
            if g02_order_id is None:
                raise ValueError("pos_id is None")
            
            local_pos_id = open_positions[0] if open_positions else g02_order_id
            api.close_position(local_pos_id)
            time.sleep(2)
            
            # Validate closure
            check, new_data = api.get_order(g02_order_id)
            if check and isinstance(new_data, dict):
                status = new_data.get("status", "")
                assert status == "closed" or new_data.get("position_status") == "closed", f"Status is not closed: {status}"
            
            # Remove from cleanup since it's closed
            if local_pos_id in open_positions:
                open_positions.remove(local_pos_id)
                
            collector.record(TestResult(SUITE_NAME, "G-05: Close position manually", "PASSED", detail="Position closed", duration=time.time() - start))
        except Exception as e:
            collector.record(TestResult(SUITE_NAME, "G-05: Close position manually", "FAILED", detail=str(e), duration=time.time() - start))

        time.sleep(2)

        # Test G-06: Buy order — PUT side
        start = time.time()
        try:
            check, put_order_id = api.buy_order(
                instrument_type=category,
                instrument_id=asset,
                side="sell", # put
                amount=PRACTICE_AMOUNT,
                leverage=1,
                type="market",
                limit_price=None,
                stop_price=None,
                stop_lose_kind="percent",
                stop_lose_value=5.0,
                take_profit_kind="percent",
                take_profit_value=10.0
            )
            assert check, f"CFD put order failed. Order_id: {put_order_id}"
            
            put_pos_id = put_order_id
            time.sleep(1)
            o_check, o_data = api.get_order(put_order_id)
            if o_check and isinstance(o_data, dict):
                put_pos_id = o_data.get("position_id", put_order_id)
                
            open_positions.append(put_pos_id)
            
            time.sleep(1)
            # Close it intentionally now to keep it clean
            api.close_position(put_pos_id)
            
            # Verify close
            time.sleep(2)
            check_cls, c_data = api.get_order(put_order_id)
            if check_cls and isinstance(c_data, dict):
                 assert c_data.get("status") == "closed" or c_data.get("position_status") == "closed", "Failed to close PUT order immediately"
                 open_positions.remove(put_pos_id)
            
            collector.record(TestResult(SUITE_NAME, "G-06: Buy order \u2014 PUT side", "PASSED", detail=f"ID: {put_order_id} opened & closed", duration=time.time() - start))
        except Exception as e:
            collector.record(TestResult(SUITE_NAME, "G-06: Buy order \u2014 PUT side", "FAILED", detail=str(e), duration=time.time() - start))

    finally:
        # CLEANUP: Ensure any remaining tracked positions do not linger and bleed practice balance
        if open_positions:
            logger.warning(f"Suite G Cleanup: Aborting {len(open_positions)} stranded CFD positions!")
            for pos_id in open_positions:
                try:
                    logger.info(f"Issuing fallback close_position() on {pos_id}")
                    api.close_position(pos_id)
                    time.sleep(0.5)
                except Exception as ex:
                    logger.error(f"Cleanup failed for position {pos_id}: {ex}")
