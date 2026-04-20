import os
from typing import Optional

# Wait, we need the IQ_Option type
# but we shouldn't import it directly at the top level to avoid circular issues or delayed imports in some cases,
# actually the spec says: "The config module must also define a shared api_instance: IQ_Option | None = None."
# I'll just use 'Any' or import it conditionally, but 'from iqoptionapi.stable_api import IQ_Option' is fine safely.
from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv

load_dotenv()

# Load credentials from environment
IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

if not IQ_EMAIL or not IQ_PASSWORD:
    raise RuntimeError("Missing required environment variables: IQ_EMAIL and IQ_PASSWORD")

PRACTICE_ASSET_BINARY = os.getenv("PRACTICE_ASSET_BINARY", "EURUSD-OTC")
PRACTICE_ASSET_DIGITAL = os.getenv("PRACTICE_ASSET_DIGITAL", "EURUSD-OTC")
PRACTICE_ASSET_CFD = os.getenv("PRACTICE_ASSET_CFD", "EURUSD")
PRACTICE_AMOUNT = float(os.getenv("PRACTICE_AMOUNT", "1.0"))
PRACTICE_TIMEOUT = int(os.getenv("PRACTICE_TIMEOUT", "120"))

# Shared API instance state
api_instance: Optional[IQ_Option] = None
