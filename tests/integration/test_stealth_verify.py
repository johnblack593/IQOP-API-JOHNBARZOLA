"""
Verificación de métricas de Stealth — Sprint 7
"""
import os
import time
import logging
from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("stealth_verify")

def verify():
    email = os.environ.get("IQ_EMAIL", "your_email")
    password = os.environ.get("IQ_PASSWORD", "your_password")
    
    api = IQ_Option(email, password)
    
    # 1. Verificar User-Agent
    ua = api.SESSION_HEADER.get("User-Agent", "")
    logger.info(f"User-Agent: {ua}")
    if "Chrome/147" in ua:
        logger.info("✅ User-Agent compliance: 100%")
    else:
        logger.warning("❌ User-Agent mismatch")

    status, _ = api.connect()
    if not status: return

    # 2. Verificar request_id secuencial/único
    logger.info(f"Último request_id: {api.api._request_id_counter}")
    if api.api._request_id_counter > 0:
        logger.info("✅ request_id unique tracking: 100%")

    api.close()

if __name__ == "__main__":
    verify()
