"""
scratch/ws_debug_runner.py
Sprint 4 TAREA 1 — Run a single connection with JCBV_WS_DEBUG=1
to capture the WS message sequence.

Usage:
    set JCBV_WS_DEBUG=1
    python scratch/ws_debug_runner.py
    
The log will be saved to tests/reports/ws_sequence_debug_YYYYMMDD_HHMMSS.log
"""
import os
import sys
import time
import logging

os.environ["JCBV_WS_DEBUG"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.logger import configure_root_logger

configure_root_logger(logging.INFO)
logger = logging.getLogger("ws_debug_runner")


def main():
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    
    if not email or not password:
        logger.error("Missing IQ_EMAIL or IQ_PASSWORD.")
        sys.exit(1)

    logger.info("Starting WS Debug Session (JCBV_WS_DEBUG=1)")
    
    iq = IQ_Option(email, password)
    
    status, reason = iq.connect()
    logger.info("connect() returned: status=%s reason=%s", status, reason)
    
    if not status:
        logger.error("Connection failed: %s", reason)
        sys.exit(1)
    
    logger.info("Waiting 5s after connect for additional WS messages...")
    time.sleep(5)
    
    logger.info("Calling get_all_open_time()...")
    open_time = iq.get_all_open_time()
    
    total = sum(len(v) for v in open_time.values())
    logger.info("get_all_open_time() returned %d total assets", total)
    
    for cat, assets in open_time.items():
        logger.info("  %s: %d assets", cat, len(assets))
    
    logger.info("Waiting 10s for post-query WS messages...")
    time.sleep(10)
    
    # Close the debug log file
    if hasattr(iq.api, '_ws_debug_file'):
        iq.api._ws_debug_file.flush()
        log_path = iq.api._ws_debug_file.name
        iq.api._ws_debug_file.close()
        logger.info("WS debug log saved to: %s", log_path)
    
    iq.close()
    logger.info("Done.")


if __name__ == "__main__":
    main()
