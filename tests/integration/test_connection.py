"""
tests/integration/test_connection.py
───────────────────────────────────
Smoke tests verifying real connectivity with IQ Option.
"""

import os
import pytest
import time
from iqoptionapi.stable_api import IQ_Option


@pytest.mark.integration
def test_connect_practice_account():
    """Verifica que la API conecta al servidor de IQ Option."""
    email = os.environ.get("IQOP_EMAIL")
    password = os.environ.get("IQOP_PASSWORD")
    if not email or not password:
        pytest.skip("IQOP_EMAIL / IQOP_PASSWORD not set")
    
    api = IQ_Option(email, password, "PRACTICE")
    connected, reason = api.connect()
    try:
        assert connected is True, f"Connection failed: {reason}"
    finally:
        api.close()


@pytest.mark.integration
def test_get_balance_after_connect():
    """Verifica que el balance practice es accesible post-connect."""
    email = os.environ.get("IQOP_EMAIL")
    password = os.environ.get("IQOP_PASSWORD")
    if not email or not password:
        pytest.skip("IQOP_EMAIL / IQOP_PASSWORD not set")
    
    api = IQ_Option(email, password, "PRACTICE")
    connected, _ = api.connect()
    try:
        assert connected is True
        balance = api.get_balance()
        assert isinstance(balance, (int, float))
        assert balance >= 0
    finally:
        api.close()


@pytest.mark.integration
def test_server_timestamp_is_recent():
    """Verifica que el timestamp del servidor es Unix reciente."""
    email = os.environ.get("IQOP_EMAIL")
    password = os.environ.get("IQOP_PASSWORD")
    if not email or not password:
        pytest.skip("IQOP_EMAIL / IQOP_PASSWORD not set")
    
    api = IQ_Option(email, password, "PRACTICE")
    connected, _ = api.connect()
    try:
        assert connected is True
        ts = api.get_server_timestamp()
        assert ts is not None
        # Allow 60s drift for CI lag or sync differences
        assert abs(ts - time.time()) < 60, "Server timestamp drift > 60s"
    finally:
        api.close()
