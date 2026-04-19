"""
iqoptionapi/http/session.py
Shared requests.Session factory with enforced TLS certificate verification
and connection pool reuse. All HTTP modules must obtain their session
through this factory — never instantiate requests.Session() directly.
"""
import certifi
import requests
from iqoptionapi.logger import get_logger

logger = get_logger(__name__)

_shared_session: requests.Session | None = None


def get_shared_session() -> requests.Session:
    """
    Return the process-level shared requests.Session.
    Creates it on first call with enforced certifi CA bundle and
    connection pool settings appropriate for a trading API client.
    Thread-safe for read access after initialization.
    """
    global _shared_session
    if _shared_session is None:
        session = requests.Session()
        session.verify = certifi.where()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=4,
            pool_maxsize=10,
            max_retries=0,        # Retries handled by ReconnectManager — never by requests
        )
        session.mount("https://", adapter)
        session.mount("http://",  adapter)
        logger.info(
            "HTTP session initialized — TLS verify=%s",
            session.verify
        )
        _shared_session = session
    return _shared_session


def close_shared_session() -> None:
    """Release the shared session. Call on application shutdown."""
    global _shared_session
    if _shared_session is not None:
        _shared_session.close()
        _shared_session = None
        logger.info("HTTP session closed.")
