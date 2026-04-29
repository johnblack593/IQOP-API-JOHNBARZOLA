"""Module for IQ option websocket."""
import logging
import iqoptionapi.core.constants as OP_code
from threading import Thread

logger = logging.getLogger(__name__)

def live_deal_digital_option(api, message):
    if message["name"] == "live-deal-digital-option":
        active_id = message["msg"].get("instrument_active_id")
        if active_id is None:
            return
        try:
            active = list(OP_code.ACTIVES.keys())[
                list(OP_code.ACTIVES.values()).index(active_id)]
        except ValueError:
            logger.debug("live_deal_digital: unknown active_id %s", active_id)
            return
        _type = message["msg"].get("expiration_type")
        if hasattr(api, 'digital_live_deal_cb') and callable(api.digital_live_deal_cb):
            cb_data = {"active": active, **message["msg"]}
            realdigital = Thread(target=api.digital_live_deal_cb, kwargs=cb_data)
            realdigital.daemon = True
            realdigital.start()

