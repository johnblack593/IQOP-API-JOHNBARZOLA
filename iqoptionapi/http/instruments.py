"""
iqoptionapi/http/instruments.py
Instrument discovery fallback — synthesizes instrument data from
initialization-data when WS get-instruments returns empty lists.

SPRINT-14 CONTEXT:
  - WS get-instruments returns instruments:[] for user_group_id:191
  - No REST HTTP endpoint exists for instrument discovery (all return 404)
  - Binary/turbo init data contains ALL underlying actives with:
    group_id (1=forex, 16=crypto, 2=equities, 3=commodities, 4=indices)
    active_id, name, schedule, enabled, is_suspended, ticker
  - This module extracts and classifies actives from init data to provide
    a transparent fallback for get_instruments()
"""

from iqoptionapi.logger import get_logger

logger = get_logger(__name__)

# Mapping from init-data group_id to instrument_type
# Discovered via SPRINT-14 PASO-1D diagnostic:
#   group_1  = forex (187 actives)
#   group_16 = crypto currencies (118 actives)
#   group_2  = equities / stocks (105)
#   group_3  = commodities (31)
#   group_4  = indices (44)
#   group_5  = industrials
#   group_7  = information technology
#   group_8  = consumer discretionary
#   group_13 = energy
#   ...etc (all non-forex/crypto are classified as "cfd")
GROUP_ID_TO_TYPE = {
    1: "forex",
    16: "crypto",
    2: "stocks",
    3: "commodities",
    4: "indices",
    41: "etf",
}

# All other group_ids map to "cfd"
_CFD_GROUP_IDS = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                  17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
                  29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
                  41, 42, 43, 44, 45, 46}


def _classify_type(group_id: int) -> str:
    """Map a group_id from init-data to an instrument_type string."""
    return GROUP_ID_TO_TYPE.get(group_id, "cfd")


def _extract_instruments_from_init(init_data: dict, instrument_type: str) -> list:
    """
    Parse binary/turbo actives from initialization-data and return
    instruments matching the requested type.

    Args:
        init_data: The dict returned by get_all_init_v2() or get_all_init().
                   Expected structure: {"binary": {"actives": {id: {...}}}, ...}
        instrument_type: One of "forex", "cfd", "crypto"

    Returns:
        List of instrument dicts compatible with WS format:
        [{"id": "EURUSD", "active_id": 1, "name": "EURUSD", "schedule": [...], ...}]
    """
    instruments = []
    seen_tickers = set()  # Deduplicate across binary/turbo

    for category in ("binary", "turbo"):
        actives = {}
        cat_data = init_data.get(category, {})

        if isinstance(cat_data, dict):
            actives = cat_data.get("actives", {})
        # Handle classic init format: init_data["result"]["binary"]["actives"]
        elif "result" in init_data:
            actives = init_data.get("result", {}).get(category, {}).get("actives", {})

        for active_id_str, info in actives.items():
            if not isinstance(info, dict):
                continue

            group_id = info.get("group_id")
            if group_id is None:
                continue

            classified_type = _classify_type(group_id)
            if classified_type != instrument_type:
                continue

            # Extract clean ticker name
            raw_name = info.get("name", "")
            # Strip "front." prefix: "front.EURUSD" → "EURUSD"
            name_clean = raw_name.replace("front.", "")
            # Use explicit ticker field if it looks valid (not just a suffix)
            ticker_field = info.get("ticker", "")
            if ticker_field and len(ticker_field) > 3 and ticker_field not in ("OTC",):
                ticker = ticker_field
            else:
                ticker = name_clean

            # Skip entries with empty or unusable tickers
            if not ticker or len(ticker) < 2:
                continue

            if ticker in seen_tickers:
                continue
            seen_tickers.add(ticker)

            # Normalize schedule from init format [start, end] to WS format {open, close}
            raw_schedule = info.get("schedule", [])
            schedule = []
            for entry in raw_schedule:
                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    schedule.append({"open": entry[0], "close": entry[1]})
                elif isinstance(entry, dict):
                    schedule.append(entry)

            instruments.append({
                "id": ticker,
                "active_id": int(active_id_str) if str(active_id_str).isdigit() else info.get("id", 0),
                "name": ticker,
                "description": info.get("description", "").replace("front.", ""),
                "ticker": ticker,
                "group_id": group_id,
                "enabled": info.get("enabled", False),
                "is_suspended": info.get("is_suspended", False),
                "precision": info.get("precision", 6),
                "schedule": schedule,
                # Metadata for debugging
                "_source": "init-data-fallback",
                "_category": category,
            })

    return instruments


def get_instruments_from_init(api_instance, instrument_type: str) -> dict:
    """
    High-level fallback: fetches instruments by extracting from init data.

    Args:
        api_instance: The IQ_Option (stable_api) instance with active connection
        instrument_type: "forex", "cfd", or "crypto"

    Returns:
        Dict compatible with WS response: {"instruments": [...]}
    """
    try:
        # Try modern init first (get-initialization-data v3)
        init_data = api_instance.get_all_init_v2()
        if init_data:
            instruments = _extract_instruments_from_init(init_data, instrument_type)
            if instruments:
                logger.info(
                    "Init-data fallback: extracted %d %s instruments from init_v2",
                    len(instruments), instrument_type
                )
                return {"instruments": instruments}

        # Fallback to classic init (api_option_init_all)
        init_data = api_instance.get_all_init()
        if init_data and "result" in init_data:
            instruments = _extract_instruments_from_init(
                init_data["result"], instrument_type
            )
            if instruments:
                logger.info(
                    "Init-data fallback: extracted %d %s instruments from classic init",
                    len(instruments), instrument_type
                )
                return {"instruments": instruments}

        logger.warning(
            "Init-data fallback: no %s instruments found in any init source",
            instrument_type
        )
        return {"instruments": []}

    except Exception as e:
        logger.error(
            "Init-data fallback failed for %s: %s", instrument_type, e
        )
        return {"instruments": []}
