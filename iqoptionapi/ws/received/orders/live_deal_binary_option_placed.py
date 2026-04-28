"""Module for IQ option websocket."""
import logging
import iqoptionapi.constants as OP_code
from threading import Thread

logger = logging.getLogger(__name__)

def live_deal_binary_option_placed(api, message):
    if message["name"] == "live-deal-binary-option-placed":
        active_id = message["msg"].get("active_id")
        if active_id is None:
            return
        try:
            active = list(OP_code.ACTIVES.keys())[
                list(OP_code.ACTIVES.values()).index(active_id)]
        except ValueError:
            logger.debug("live_deal_binary: unknown active_id %s", active_id)
            return
        _type = message["msg"].get("option_type")
        if hasattr(api, 'binary_live_deal_cb') and callable(api.binary_live_deal_cb):
            cb_data = {"active": active, **message["msg"]}
            realbinary = Thread(target=api.binary_live_deal_cb, kwargs=cb_data)
            realbinary.daemon = True
            realbinary.start()
