"""
Unit tests for iqoptionapi/health.py.
"""

import json
import time
import urllib.request
from unittest.mock import MagicMock

import pytest
import iqoptionapi
from iqoptionapi.health import HealthCheckServer


def test_server_starts_and_responds():
    """Levantar HealthCheckServer(iq=None, port=0) y verificar GET /health."""
    server = HealthCheckServer(iq=None, port=0)
    server.start()
    try:
        url = f"http://127.0.0.1:{server.port}/health"
        with urllib.request.urlopen(url) as response:
            assert response.status == 200
            data = json.loads(response.read().decode("utf-8"))
            assert data["status"] == "ok"
    finally:
        server.stop()


def test_response_contains_required_keys():
    """Verificar que el JSON contiene todas las llaves requeridas."""
    server = HealthCheckServer(iq=None, port=0)
    server.start()
    try:
        url = f"http://127.0.0.1:{server.port}/health"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            required_keys = {
                "status", "version", "connected", "balance_id",
                "server_timestamp", "circuit_breaker", "uptime_seconds"
            }
            assert set(data.keys()) == required_keys
    finally:
        server.stop()


def test_connected_false_when_iq_none():
    """Con iq=None, 'connected' debe ser False."""
    server = HealthCheckServer(iq=None, port=0)
    server.start()
    try:
        url = f"http://127.0.0.1:{server.port}/health"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            assert data["connected"] is False
    finally:
        server.stop()


def test_version_matches_package():
    """'version' debe ser == iqoptionapi.__version__."""
    server = HealthCheckServer(iq=None, port=0)
    server.start()
    try:
        url = f"http://127.0.0.1:{server.port}/health"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            assert data["version"] == iqoptionapi.__version__
    finally:
        server.stop()


def test_uptime_increases():
    """Hacer dos requests; el segundo uptime_seconds debe ser mayor."""
    server = HealthCheckServer(iq=None, port=0)
    server.start()
    try:
        url = f"http://127.0.0.1:{server.port}/health"
        
        with urllib.request.urlopen(url) as response:
            data1 = json.loads(response.read().decode("utf-8"))
        
        time.sleep(0.2)
        
        with urllib.request.urlopen(url) as response:
            data2 = json.loads(response.read().decode("utf-8"))
            
        assert data2["uptime_seconds"] > data1["uptime_seconds"]
    finally:
        server.stop()


def test_stop_terminates_thread():
    """Llamar stop(); verificar is_running() == False."""
    server = HealthCheckServer(iq=None, port=0)
    server.start()
    assert server.is_running() is True
    server.stop()
    # give some time for thread to die if needed, though shutdown is synchronous
    assert server.is_running() is False


def test_double_start_no_exception(caplog):
    """Llamar start() dos veces; no debe lanzar excepción, debe loguear warning."""
    import logging
    logger = logging.getLogger("iqoptionapi")
    old_propagate = logger.propagate
    logger.propagate = True
    server = HealthCheckServer(iq=None, port=0)
    server.start()
    try:
        with caplog.at_level(logging.WARNING, logger="iqoptionapi.health"):
            server.start()
        assert any("HealthCheckServer is already running." in r.message for r in caplog.records)
    finally:
        server.stop()
        logger.propagate = old_propagate


def test_circuit_breaker_unknown_when_iq_none():
    """Con iq=None, 'circuit_breaker' debe ser 'unknown'."""
    server = HealthCheckServer(iq=None, port=0)
    server.start()
    try:
        url = f"http://127.0.0.1:{server.port}/health"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            assert data["circuit_breaker"] == "unknown"
    finally:
        server.stop()


def test_connected_logic_with_mock():
    """Test connected logic when iq has api and timesync."""
    mock_iq = MagicMock()
    # Mock iq.api.timesync.server_timestamp
    mock_iq.api.timesync.server_timestamp = 1700000000
    mock_iq.get_balance_id.return_value = 888
    mock_iq.get_server_timestamp.return_value = 1700000000
    mock_iq.circuit_breaker.is_open.return_value = False

    server = HealthCheckServer(iq=mock_iq, port=0)
    server.start()
    try:
        url = f"http://127.0.0.1:{server.port}/health"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            assert data["connected"] is True
            assert data["balance_id"] == 888
            assert data["server_timestamp"] == 1700000000
            assert data["circuit_breaker"] == "closed"
    finally:
        server.stop()
