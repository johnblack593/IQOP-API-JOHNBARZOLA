"""Module for IQ option websocket."""
import logging
import iqoptionapi.core.constants as OP_code
from threading import Thread

logger = logging.getLogger(__name__)

def live_deal(api, message):
    if message["name"] == "live-deal":
        active_id = message["msg"].get("instrument_active_id")
        if active_id is None:
            return
        try:
            active = list(OP_code.ACTIVES.keys())[
                list(OP_code.ACTIVES.values()).index(active_id)]
        except ValueError:
            logger.debug("live_deal: unknown active_id %s", active_id)
            return
        _type = message["msg"].get("instrument_type")
        if hasattr(api, 'live_deal_cb') and callable(api.live_deal_cb):
            cb_data = {"active": active, **message["msg"]}
            livedeal = Thread(target=api.live_deal_cb, kwargs=cb_data)
            livedeal.daemon = True
            livedeal.start()

