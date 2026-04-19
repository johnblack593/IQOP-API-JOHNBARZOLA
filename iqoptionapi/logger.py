# iqoptionapi/logger.py
# Factory for IQOP-API-JOHNBARZOLA structured logging
# SECURITY NOTE: Never pass credentials (email, password, ssid) to any logger call.
# Sanitize all dict payloads before logging. Use logger.debug() for WS payloads
# only in development environments; disable DEBUG in production.

import logging
import sys
from typing import Optional

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-35s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Call once at application startup to configure the root logger.
    Sets up a StreamHandler to stdout with structured format.
    """
    root = logging.getLogger("iqoptionapi")
    if root.handlers:
        return  # Prevent duplicate handlers if called multiple times
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.setLevel(level)
    root.addHandler(handler)
    root.propagate = False

def get_logger(name: str) -> logging.Logger:
    """
    Factory function. Usage: logger = get_logger(__name__)
    """
    configure_root_logger()
    return logging.getLogger(name)
