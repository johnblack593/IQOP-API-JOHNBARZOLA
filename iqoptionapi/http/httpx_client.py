import httpx
import certifi
from iqoptionapi.logger import get_logger

logger = get_logger(__name__)

class HTTPXClient:
    """
    Sprint 5: Hardened HTTP/2 client with Chrome 147 parity headers.
    Ensures that authentication requests look exactly like the browser.
    """
    def __init__(self):
        self.client = httpx.Client(
            http2=True,
            verify=certifi.where(),
            follow_redirects=True,
            timeout=15.0
        )
        self.headers = {
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
        self.client.headers.update(self.headers)

    def post(self, url, data=None, json=None, headers=None):
        try:
            return self.client.post(url, data=data, json=json, headers=headers)
        except Exception as e:
            logger.error(f"HTTPX POST error: {e}")
            raise

    def get(self, url, params=None, headers=None):
        try:
            return self.client.get(url, params=params, headers=headers)
        except Exception as e:
            logger.error(f"HTTPX GET error: {e}")
            raise

    def close(self):
        self.client.close()
