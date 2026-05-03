"""
Health check module for IQ Option API.
Provides a minimal HTTP server to monitor bot status.
"""

import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING

import iqoptionapi

if TYPE_CHECKING:
    from iqoptionapi.stable_api import IQ_Option

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    HTTP handler for the health check endpoint.
    """

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_health(self):
        """Generate and send the health status JSON."""
        server: "HealthCheckServer" = self.server.health_server  # type: ignore
        iq = server.iq
        start_time = server.start_time

        status_data = {
            "status": "ok",
            "version": iqoptionapi.__version__,
            "connected": False,
            "balance_id": None,
            "server_timestamp": None,
            "circuit_breaker": "unknown",
            "uptime_seconds": 0.0,
        }

        try:
            if start_time:
                status_data["uptime_seconds"] = round(time.time() - start_time, 2)

            if iq:
                # Connected check: iq.api exists and has a timestamp
                is_connected = False
                try:
                    if hasattr(iq, "api") and iq.api and iq.api.timesync.server_timestamp > 0:
                        is_connected = True
                except Exception:
                    pass

                status_data["connected"] = is_connected

                if is_connected:
                    try:
                        status_data["balance_id"] = iq.get_balance_id()
                    except Exception:
                        pass
                    
                    try:
                        status_data["server_timestamp"] = iq.get_server_timestamp()
                    except Exception:
                        pass

                # Circuit breaker check
                try:
                    if hasattr(iq, "circuit_breaker") and iq.circuit_breaker:
                        status_data["circuit_breaker"] = (
                            "open" if iq.circuit_breaker.is_open() else "closed"
                        )
                except Exception:
                    pass
        except Exception as e:
            logger.error("Error building health status: %s", e)

        # Send response
        try:
            response_body = json.dumps(status_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except Exception as e:
            logger.error("Error sending health response: %s", e)

    def log_message(self, format, *args):
        """Silences standard HTTP logging to avoid cluttering bot logs."""
        return


class HealthCheckServer:
    """
    Standalone HTTP server for health monitoring.
    Runs in a daemon thread.
    """

    def __init__(
        self,
        iq: "IQ_Option | None" = None,
        port: int = 8765,
        host: str = "127.0.0.1",
    ):
        self.iq = iq
        self.port = port
        self.host = host
        self.server: HTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.start_time: float | None = None

    def start(self):
        """Starts the health check server in a daemon thread."""
        if self.thread and self.thread.is_alive():
            logger.warning("HealthCheckServer is already running.")
            return

        try:
            self.server = HTTPServer((self.host, self.port), HealthCheckHandler)
            self.server.health_server = self  # type: ignore
            self.start_time = time.time()

            self.thread = threading.Thread(
                target=self.server.serve_forever,
                name="iqopt-health",
                daemon=True,
            )
            self.thread.start()
            
            # Update port in case it was 0
            self.port = self.server.server_address[1]
            logger.info("HealthCheckServer started at http://%s:%s/health", self.host, self.port)
        except Exception as e:
            logger.error("Failed to start HealthCheckServer: %s", e)

    def stop(self):
        """Stops the health check server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("HealthCheckServer stopped.")
        
        self.server = None
        self.thread = None
        self.start_time = None

    def is_running(self) -> bool:
        """Returns True if the server thread is alive."""
        return self.thread is not None and self.thread.is_alive()


if __name__ == "__main__":
    # Demo block
    logging.basicConfig(level=logging.INFO)
    hc = HealthCheckServer(iq=None, port=8765)
    hc.start()
    print(f"Health check server running at http://127.0.0.1:{hc.port}/health")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        hc.stop()
