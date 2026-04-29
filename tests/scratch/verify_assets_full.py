"""
scratch/verify_assets_full.py
Sprint 4 — Verificación Final de Asset Discovery

Conecta sin WARP, espera init-data, y verifica conteo de activos.
Uso:
    python scratch/verify_assets_full.py

Credenciales desde .env (IQ_EMAIL, IQ_PASSWORD)
"""
import os
import sys
import time
import logging

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.core.logger import configure_root_logger

configure_root_logger(logging.INFO)
logger = logging.getLogger("verify_assets_full")

fh = logging.FileHandler("scratch/verify_log.txt", mode="w", encoding="utf-8")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# ── Thresholds ──
EXPECTED = {
    "binary":      100,
    "turbo":       100,
    "blitz":       100,
    "digital":      50,
    "forex":        20,
    "stocks":       50,
    "crypto":       30,
    "indices":      20,
    "commodities":  10,
}


def main():
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    
    if not email or not password:
        logger.error("Missing IQ_EMAIL or IQ_PASSWORD environment variables.")
        sys.exit(1)

    logger.info("═══════════════════════════════════════════════════")
    logger.info("  Sprint 4 — Full Asset Verification (v8.9.995)")
    logger.info("═══════════════════════════════════════════════════")
    
    iq = IQ_Option(email, password)
    
    logger.info("Connecting WITHOUT WARP...")
    t_start = time.time()
    status, reason = iq.connect()
    t_connect = time.time() - t_start
    
    if not status:
        logger.error("Connection FAILED: %s (after %.1fs)", reason, t_connect)
        sys.exit(1)
    
    logger.info("Connected in %.1fs", t_connect)
    
    # _wait_for_init_data was already called inside connect()
    # Verify it worked
    init = getattr(iq.api, 'api_option_init_all_result_v2', None)
    if init and isinstance(init, dict):
        binary_count = len(init.get("binary", {}).get("actives", {}))
        turbo_count = len(init.get("turbo", {}).get("actives", {}))
        logger.info("Init data loaded: binary=%d turbo=%d actives", binary_count, turbo_count)
    else:
        logger.warning("Init data NOT available after connect()")

    logger.info("Calling get_all_open_time()...")
    t_start = time.time()
    open_time = iq.get_all_open_time()
    t_open = time.time() - t_start
    logger.info("get_all_open_time() completed in %.1fs", t_open)

    # ── Count and verify ──
    logger.info("")
    logger.info("═══════════════════════════════════════════════════")
    logger.info("  ASSET COUNT RESULTS")
    logger.info("═══════════════════════════════════════════════════")
    
    all_passed = True
    total = 0

    with open("scratch/results.txt", "w", encoding="utf-8") as rf:
        rf.write(f"binary: {len(open_time.get('binary', {}))}\n")
        rf.write(f"turbo: {len(open_time.get('turbo', {}))}\n")
        rf.write(f"digital: {len(open_time.get('digital', {}))}\n")
        rf.write(f"forex: {len(open_time.get('forex', {}))}\n")
        rf.write(f"crypto: {len(open_time.get('crypto', {}))}\n")
        rf.write(f"cfd: {len(open_time.get('cfd', {}))}\n")
        for category, threshold in EXPECTED.items():
            assets = open_time.get(category, {})
            count = len(assets)
            open_count = sum(1 for v in assets.values() if isinstance(v, dict) and v.get("open"))
            total += count
            
            status_str = "✅ PASS" if count >= threshold else "❌ FAIL"
            if count < threshold:
                all_passed = False
            
            msg = "  %-14s %4d total / %4d open  (need>%d)  %s" % (category, count, open_count, threshold, status_str)
            logger.info(msg)
            rf.write(msg + "\n")
        
        logger.info("")
        logger.info("  TOTAL: %d assets across all categories", total)
        logger.info("═══════════════════════════════════════════════════")
        rf.write(f"TOTAL: {total}\n")
        
        if all_passed:
            logger.info("  🏆 ALL CATEGORIES PASSED — Sprint 4 VERIFIED")
            rf.write("ALL PASSED\n")
        else:
            logger.warning("  ⚠️  Some categories below threshold — review needed")
            rf.write("SOME FAILED\n")
        
        logger.info("═══════════════════════════════════════════════════")
    
    # Cleanup
    iq.close()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

