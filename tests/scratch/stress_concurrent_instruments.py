"""
scratch/stress_concurrent_instruments.py
Sprint 6 — Concurrent Stress Test for Asset Discovery

1. Connects without WARP
2. Calls get_all_open_time() 3 times consecutively with 5s delay
3. Verifies that forex/cfd/crypto counts DO NOT degrade (are >= previous count and > 0)
"""
import os
import sys
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.core.logger import configure_root_logger

configure_root_logger(logging.INFO)
logger = logging.getLogger("stress_concurrent_instruments")

fh = logging.FileHandler("scratch/stress_log.txt", mode="w", encoding="utf-8")
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
    logger.info("  Sprint 6 — Concurrent Stress Test (v9.0.0)")
    logger.info("═══════════════════════════════════════════════════")
    
    iq = IQ_Option(email, password)
    
    logger.info("Connecting WITHOUT WARP...")
    status, reason = iq.connect()
    
    if not status:
        logger.error("Connection FAILED: %s", reason)
        sys.exit(1)
    
    logger.info("Connected successfully.")
    
    # Run get_all_open_time() 3 times
    previous_counts = {"forex": 0, "cfd": 0, "crypto": 0}
    iterations = 3
    all_passed = True
    
    for i in range(1, iterations + 1):
        logger.info("\n--- Iteration %d ---", i)
        
        t_start = time.time()
        open_time = iq.get_all_open_time()
        t_open = time.time() - t_start
        logger.info("get_all_open_time() completed in %.1fs", t_open)
        
        current_counts = {
            "forex": len(open_time.get("forex", {})),
            "cfd": len(open_time.get("cfd", {})),
            "crypto": len(open_time.get("crypto", {}))
        }
        
        logger.info("Counts: Forex=%d, CFD=%d, Crypto=%d", 
                    current_counts["forex"], current_counts["cfd"], current_counts["crypto"])
        
        for cat, count in current_counts.items():
            if count == 0:
                logger.error("FAIL: %s count is 0!", cat)
                all_passed = False
            if count < previous_counts[cat]:
                logger.error("FAIL: %s degraded from %d to %d!", cat, previous_counts[cat], count)
                all_passed = False
                
        previous_counts = current_counts
        
        if i < iterations:
            logger.info("Waiting 5s...")
            time.sleep(5)
            
    logger.info("═══════════════════════════════════════════════════")
    if all_passed:
        logger.info("  🏆 STRESS TEST PASSED")
    else:
        logger.error("  ❌ STRESS TEST FAILED")
        
    iq.close()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

