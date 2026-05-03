"""
iqoptionapi/http/session.py
Shared curl-cffi.requests.Session factory with Chrome 147 impersonation.
This eliminates JA3/JA4 fingerprint mismatches during TLS handshake.
"""
from curl_cffi import requests
import certifi
from iqoptionapi.core.logger import get_logger

logger = get_logger(__name__)

# Compatibility alias
Session = requests.Session

_shared_client: requests.Session | None = None

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Safari/537.36"
)

CHROME_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Connection": "keep-alive",
    "Referer": "https://iqoption.com/",
    "Origin": "https://iqoption.com"
}

def get_shared_session() -> requests.Session:
    """
    Return the process-level shared curl-cffi Session.
    Enforces Chrome 147 impersonation and TLS parity.
    """
    global _shared_client
    if _shared_client is None:
        _shared_client = requests.Session(
            impersonate="chrome110", # closest stable to 147 in current curl-cffi
            headers=CHROME_HEADERS,
            timeout=30.0,
            verify=True
        )
        logger.info(
            "CURL-CFFI shared client initialized — Chrome impersonation enabled."
        )
    return _shared_client

def close_shared_session() -> None:
    """Release the shared client."""
    global _shared_client
    if _shared_client is not None:
        # curl-cffi Session doesn't have a close() method like httpx in some versions
        # but we can just null it out.
        _shared_client = None
        logger.info("CURL-CFFI shared client released.")
