"""Module for IQ option websocket."""
import logging
import iqoptionapi.constants as OP_code

logger = logging.getLogger(__name__)

def instrument_quotes_generated(api, message):
    if message["name"] == "instrument-quotes-generated":
        msg = message.get("msg", {})
        active_id = msg.get("active")
        if active_id is None:
            return

        try:
            Active_name = list(OP_code.ACTIVES.keys())[
                list(OP_code.ACTIVES.values()).index(active_id)]
        except ValueError:
            logger.debug("instrument_quotes: unknown active_id %s", active_id)
            return

        period = msg.get("expiration", {}).get("period")
        ans = {}
        for data in msg.get("quotes", []):
            # FROM IQ OPTION SOURCE CODE
            ask_price = data.get("price", {}).get("ask")
            if ask_price is None:
                ProfitPercent = None
            else:
                askPrice = float(ask_price)
                ProfitPercent = ((100 - askPrice) * 100) / askPrice if askPrice != 0 else None

            for symble in data.get("symbols", []):
                ans[symble] = ProfitPercent

        api.instrument_quites_generated_timestamp[Active_name][
            period] = msg.get("expiration", {}).get("timestamp")
        api.instrument_quites_generated_data[Active_name][period] = ans
        api.instrument_quotes_generated_raw_data[Active_name][period] = message