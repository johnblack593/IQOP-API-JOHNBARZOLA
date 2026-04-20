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
    """
    priority = [
        "EURUSD-OTC", "GBPUSD-OTC", "AUDUSD-OTC",
        "EURUSD", "GBPUSD", "AUDUSD", "USDJPY"
    ]
    open_assets = []
    try:
        ot = api.get_all_open_time()
        
        # Binary / turbo / digital categorization
        types_to_check = [instrument_type]
        if instrument_type == "binary":
            types_to_check = ["binary", "turbo", "otc"]
            
        for t in types_to_check:
            if t in ot:
                for aid, adata in ot[t].get("actives", {}).items():
                    name = str(adata.get("name", ""))
                    if "." in name:
                        name = name.split(".")[1]
                    if adata.get("open", False):
                        if name not in open_assets:
                            open_assets.append(name)
                            
        for p in priority:
            if p in open_assets:
                return p
                
        if open_assets:
            return open_assets[0]
            
    except Exception as e:
        import logging
        logging.error(f"Error fetching open {instrument_type} assets: {e}")
        
    return None
