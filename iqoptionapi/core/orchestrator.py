"""
iqoptionapi/core/orchestrator.py
Orchestrates the connection sequence to mirror browser behavior.
Handles HTTP authentication, session retrieval, and WebSocket handshake timing.
"""
import time
import random
from iqoptionapi.http.session import get_shared_session
from iqoptionapi.core.logger import get_logger

logger = get_logger(__name__)

class ConnectionOrchestrator:
    def __init__(self, api_instance):
        self.api = api_instance
        self.session = get_shared_session()
        self.base_url = "https://iqoption.com"
        self.auth_url = "https://auth.iqoption.com"

    def pre_handshake_sequence(self):
        """
        Execute the browser-like HTTP initialization sequence.
        """
        logger.info("Starting orchestrated pre-handshake sequence...")
        
        # 1. AppInit
        try:
            resp_init = self.session.get(f"{self.base_url}/api/appinit")
            resp_init.raise_for_status()
            logger.debug("AppInit successful.")
        except Exception as e:
            logger.warning(f"AppInit failed (stealth risk): {e}")

        # Human-like delay
        time.sleep(random.uniform(0.5, 1.2))

        # 2. Check Session (Retrieves SSID if cookies are present)
        try:
            resp_session = self.session.get(f"{self.auth_url}/api/v4/check-session")
            if resp_session.status_code == 200:
                data = resp_session.json()
                ssid = data.get("id")
                if ssid:
                    logger.info(f"Session found via check-session. SSID: {ssid[:8]}...")
                    self.api.SSID = ssid
            else:
                logger.debug("No active session found via check-session.")
        except Exception as e:
            logger.debug(f"Check-session skipped or failed: {e}")

    def post_websocket_connect(self):
        """
        Execute actions required immediately after WebSocket upgrade.
        """
        logger.info("Executing post-connect synchronization...")
        # Browser usually waits a tiny bit before sending ssid
        time.sleep(random.uniform(0.1, 0.3))
        
        if self.api.SSID:
            self.api.send_ssid()
            logger.info("SSID dispatched to WebSocket.")
        else:
            logger.warning("WebSocket connected but no SSID available for handshake.")

    def inject_human_jitter(self, action_type="heartbeat"):
        """
        Calculates a jittered interval for various actions.
        """
        if action_type == "heartbeat":
            # Standard 5s heartbeat with 10% jitter
            return 5.0 + random.uniform(-0.5, 0.5)
        elif action_type == "reconnect":
            return random.uniform(2.0, 5.0)
        return 0.0
