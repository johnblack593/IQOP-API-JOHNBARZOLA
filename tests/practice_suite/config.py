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

def get_available_binary_asset(api: IQ_Option, instrument_type: str = "binary") -> Optional[str]:
    """
    Returns the name of the first available asset for binary/turbo/digital.
    Priority list forces weekend OTCs to the front, then true M-F majors.

    The open_time structure is FLAT:
        open_times[category][asset_name]["open"] = True/False
    There is NO "actives" subkey.
    """
    priority = [
        "EURUSD-OTC", "GBPUSD-OTC", "AUDUSD-OTC", "XAUUSD-OTC",
        "EURUSD", "GBPUSD", "AUDUSD", "USDJPY"
    ]

    try:
        ot = api.get_all_open_time()
        if not ot:
            return None

        if instrument_type == "digital":
            category_keys = ["digital"]
        else:
            category_keys = ["binary", "turbo"]

        # Priority pass — check preferred assets first
        for asset in priority:
            for cat in category_keys:
                cat_data = ot.get(cat, {})
                asset_info = cat_data.get(asset, {})
                if asset_info.get("open") is True:
                    return asset

        # Fallback — first open asset in any matching category
        for cat in category_keys:
            for asset_name, info in ot.get(cat, {}).items():
                if isinstance(info, dict) and info.get("open") is True:
                    return asset_name

        # Debugging inject for SPRINT-11
        if instrument_type == "digital":
            try:
                digital_keys = list(ot.get("digital", {}).keys())
                print(f"\n[DEBUG DIGITAL] Found {len(digital_keys)} digital assets. Sample 5: {digital_keys[:5]}")
                if digital_keys:
                    first_k = digital_keys[0]
                    print(f"[DEBUG DIGITAL] Example structure '{first_k}': {ot['digital'][first_k]}")
            except Exception as e:
                print(f"[DEBUG DIGITAL] Error extracting debug: {e}")

    except Exception as e:
        import logging
        logging.error(f"Error fetching open {instrument_type} assets: {e}")

    return None
