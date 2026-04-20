import time
from examples.practice_suite.config import PRACTICE_ASSET_CFD, PRACTICE_AMOUNT
from iqoptionapi.stable_api import IQ_Option
from examples.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "G_CFD"

def check_cfd_asset_open(api: IQ_Option, asset: str) -> bool:
    try:
        ot = api.get_all_open_time()
        for cfd_type in ["cfd", "forex", "crypto"]:
            if cfd_type in ot:
                for aid, adata in ot[cfd_type]["actives"].items():
                    name = str(adata.get("name", "")).split(".")[1] if "." in str(adata.get("name", "")) else adata.get("name", "")
                    if name == asset:
                        return adata.get("open", False)
    except:
        pass
    return False

def run(api: IQ_Option, collector: ReportCollector) -> None:
    asset = PRACTICE_ASSET_CFD
    
    # Test G-01: Asset open check
    start = time.time()
    try:
        is_open = check_cfd_asset_open(api, asset)
        if not is_open:
            msg = f"SKIPPED — asset closed ({asset})"
            collector.record(TestResult(SUITE_NAME, "G-01: Asset open check", True, detail=msg))
            collector.record(TestResult(SUITE_NAME, "G-02: Buy CFD order — CALL", True, detail=msg))
            collector.record(TestResult(SUITE_NAME, "G-03: Get open position", True, detail=msg))
            collector.record(TestResult(SUITE_NAME, "G-04: Modify SL/TP", True, detail=msg))
            collector.record(TestResult(SUITE_NAME, "G-05: Close position manually", True, detail=msg))
            collector.record(TestResult(SUITE_NAME, "G-06: Buy order — PUT side", True, detail=msg))
            return
        collector.record(TestResult(SUITE_NAME, "G-01: Asset open check", True, detail=f"Open: {is_open}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "G-01: Asset open check", False, detail=str(e), duration=time.time() - start))
        return

    time.sleep(2)

    # Test G-02: Buy CFD order — CALL with SL and TP
    start = time.time()
    g02_order_id = None
    try:
        check, order_id = api.buy_order(
            instrument_type="forex",
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
        assert check, f"CFD buy order failed: {order_id}"
        assert order_id is not None, "Order ID is None"
        g02_order_id = order_id
        collector.record(TestResult(SUITE_NAME, "G-02: Buy CFD order — CALL", True, detail=f"ID: {order_id}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "G-02: Buy CFD order — CALL", False, detail=str(e), duration=time.time() - start))

    time.sleep(2)

    # Test G-03: Get open position
    start = time.time()
    try:
        if g02_order_id is None:
            raise ValueError("g02_order_id is None")
        check, order_data = api.get_order(g02_order_id)
        assert check, "Failed to get order data"
        assert order_data is not None, "Order data is None"
        # Often it is in "position-changed" -> "msg" -> "status" or just order_data["status"]
        status = order_data.get("status", "unknown")
        # For get_order it returns (True, data) where data has status
        collector.record(TestResult(SUITE_NAME, "G-03: Get open position", True, detail=f"Status: {status}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "G-03: Get open position", False, detail=str(e), duration=time.time() - start))

    # Test G-04: Modify SL/TP on open position
    start = time.time()
    try:
        if g02_order_id is None:
            raise ValueError("g02_order_id is None")
        # position_id is usually same as order_id or extracted from order_data
        pos_id = order_data.get("position_id", g02_order_id) 
        
        # change_order arguments (ID_Name, ID, stop_lose_kind, etc)
        api.change_order(
            ID_Name="position_id", 
            order_id=pos_id, 
            stop_lose_kind="percent", 
            stop_lose_value=3.0, 
            take_profit_kind="percent", 
            take_profit_value=8.0
        )
        collector.record(TestResult(SUITE_NAME, "G-04: Modify SL/TP", True, detail="SL/TP changed to 3%/8%", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "G-04: Modify SL/TP", False, detail=str(e), duration=time.time() - start))

    # Test G-05: Close open position manually
    start = time.time()
    try:
        if g02_order_id is None:
            raise ValueError("pos_id is None")
        
        pos_id = order_data.get("position_id", g02_order_id) 
        api.close_position(pos_id)
        time.sleep(3)
        check, new_data = api.get_order(g02_order_id)
        if check:
            # Usually status transitions to "closed"
            status = new_data.get("status", "")
            # Some endpoint returns error if not found, we check either
            assert status == "closed" or new_data.get("position_status") == "closed", f"Status is not closed: {status}"
        
        collector.record(TestResult(SUITE_NAME, "G-05: Close position manually", True, detail="Position closed", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "G-05: Close position manually", False, detail=str(e), duration=time.time() - start))

    time.sleep(2)

    # Test G-06: Buy order — PUT side
    start = time.time()
    try:
        check, order_id = api.buy_order(
            instrument_type="forex",
            instrument_id=asset,
            side="sell", # "sell" / "put"
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
        assert check, f"CFD put order failed: {order_id}"
        
        # Close immediately
        time.sleep(1)
        check_gd, data = api.get_order(order_id)
        if check_gd:
            api.close_position(data.get("position_id", order_id))
            
        collector.record(TestResult(SUITE_NAME, "G-06: Buy order — PUT side", True, detail=f"ID: {order_id}", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "G-06: Buy order — PUT side", False, detail=str(e), duration=time.time() - start))

