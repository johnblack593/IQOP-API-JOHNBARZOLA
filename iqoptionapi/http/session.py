"""
iqoptionapi/http/session.py
Shared httpx.Client factory with enforced TLS certificate verification,
HTTP/2 support, and Chrome 147 parity headers.
"""
import httpx
import certifi
from iqoptionapi.core.logger import get_logger

logger = get_logger(__name__)

# Backward compatibility alias
Session = httpx.Client

_shared_client: httpx.Client | None = None

CHROME_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
    "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://iqoption.com/",
    "Origin": "https://iqoption.com"
}

def get_shared_session() -> httpx.Client:
    """
    Return the process-level shared httpx.Client.
    Enforces HTTP/2, Chrome headers, and certifi CA bundle.
    """
    global _shared_client
    if _shared_client is None:
        _shared_client = httpx.Client(
            http2=True,
            verify=certifi.where(),
            headers=CHROME_HEADERS,
            follow_redirects=True,
            timeout=15.0
        )
        logger.info(
            "HTTPX shared client initialized — HTTP/2 enabled, TLS verify=%s",
            certifi.where()
        )
    return _shared_client

def close_shared_session() -> None:
    """Release the shared client."""
    global _shared_client
    if _shared_client is not None:
        _shared_client.close()
        _shared_client = None
        logger.info("HTTPX shared client closed.")

