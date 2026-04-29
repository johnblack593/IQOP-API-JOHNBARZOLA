"""A python wrapper for IQ Option API."""

__version__ = "8.9.995"

import logging

def _prepare_logging():
    """Prepare logger for module IQ Option API."""
    logger = logging.getLogger(__name__)
    #https://github.com/Lu-Yi-Hsun/iqoptionapi_private/issues/1
    #try to fix this problem
    #logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.NullHandler())

    websocket_logger = logging.getLogger("websocket")
    websocket_logger.setLevel(logging.DEBUG)
    websocket_logger.addHandler(logging.NullHandler())

_prepare_logging()

# Backward compatibility aliases for Sprint 10 refactor
from iqoptionapi.core.logger import get_logger
from iqoptionapi.core.constants import *
import iqoptionapi.core.config as config
