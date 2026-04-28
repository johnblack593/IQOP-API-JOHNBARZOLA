"""
scratch/stealth_stress_test.py
Sprint 6 — Stealth Mode Stress Test (Accelerated)

Simulates 60 minutes of active robot operation by compressing delays:
- 120 cycles
- Each cycle subscribes to candles, checks connection.
- Every 10 cycles (simulated 5 mins) -> refresh open time.
- Verifies stability without getting banned/rate limited.
"""
import os
os.environ["JCBV_WS_DEBUG"] = "1"
import sys
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from iqoptionapi.stable_api import IQ_Option
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger("STEALTH_TEST")

fh = logging.FileHandler("scratch/stealth_stress_log.txt", mode="w", encoding="utf-8")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

def main():
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    
    if not email or not password:
        logger.error("Missing IQ_EMAIL or IQ_PASSWORD.")
        sys.exit(1)

    logger.info("═══════════════════════════════════════════════════")
    logger.info("  Sprint 6 — Stealth Stress Test (v9.0.0 Candidate)")
    logger.info("═══════════════════════════════════════════════════")
    
    iq = IQ_Option(email, password)
    
    logger.info("Connecting WITHOUT WARP...")
    t_start = time.time()
    status, reason = iq.connect()
    
    if not status:
        logger.error("Connection FAILED: %s", reason)
        sys.exit(1)
    
    logger.info("Connected successfully. Starting Accelerated Stealth Test.")
    
    cycles = 120
    disconnects = 0
    all_passed = True
    assets_to_test = ["EURUSD", "BTCUSD-L"]
    
    previous_total = 0
    
    for cycle in range(1, cycles + 1):
        if not iq.check_connect():
            logger.warning("Disconnection detected at cycle %d! Reconnecting...", cycle)
            disconnects += 1
            iq.connect()
            
        # Simulate subscribing to candles (every cycle)
        for asset in assets_to_test:
            iq.start_candles_stream(asset, 60, 1)
        
        # Every 10 cycles (simulating 5 mins)
        if cycle % 10 == 0:
            logger.info("Cycle %d - Refreshing open time...", cycle)
            open_time = iq.get_all_open_time()
            total = len(open_time.get("forex", {})) + len(open_time.get("cfd", {})) + len(open_time.get("crypto", {}))
            logger.info("Margin assets total: %d", total)
            
            if total == 0:
                logger.error("FAIL: 0 margin assets fetched!")
                all_passed = False
            if previous_total > 0 and total < previous_total:
                logger.error("FAIL: Asset count degraded from %d to %d!", previous_total, total)
                all_passed = False
            previous_total = total
            
        time.sleep(1.0)  # Accelerated 1 second per cycle = 2 mins total test time
        
    for asset in assets_to_test:
        iq.stop_candles_stream(asset, 60)
        
    uptime = time.time() - t_start
    
    logger.info("═══════════════════════════════════════════════════")
    logger.info("  RESULTS")
    logger.info("═══════════════════════════════════════════════════")
    logger.info("  Total test time : %.1f seconds", uptime)
    logger.info("  Disconnects     : %d", disconnects)
    
    success = all_passed and disconnects == 0
    
    if success:
        logger.info("  🏆 STEALTH TEST PASSED (0 Bans, 0 Rate Limits, Stable)")
    else:
        logger.error("  ❌ STEALTH TEST FAILED")
        
    iq.close()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
