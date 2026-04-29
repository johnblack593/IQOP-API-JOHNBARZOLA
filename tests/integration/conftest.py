"""
Fixtures de integración. Requieren .env con:
  IQ_EMAIL=tu@email.com
  IQ_PASSWORD=tu_password
  IQ_ACCOUNT_TYPE=PRACTICE
"""
import pytest
import os
from pathlib import Path

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration (requires real connection)"
    )

def _load_env():
    # Buscar .env en la raíz del proyecto
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

@pytest.fixture(scope="session")
def iq_credentials():
    email = os.environ.get("IQ_EMAIL")
    password = os.environ.get("IQ_PASSWORD")
    if not email or not password:
        pytest.skip(
            "IQ_EMAIL / IQ_PASSWORD no configurados. "
            "Crear .env en raíz del proyecto."
        )
    return {"email": email, "password": password}

@pytest.fixture(scope="session")
def connected_api(iq_credentials):
    from iqoptionapi.stable_api import IQ_Option
    api = IQ_Option(
        iq_credentials["email"],
        iq_credentials["password"]
    )
    status, reason = api.connect()
    if not status:
        pytest.skip(f"Conexión rechazada: {reason}")
    
    # Asegurar balance de práctica
    api.change_balance("PRACTICE")
    
    yield api
    
    api.disconnect()
