"""Module for IQ option websocket."""

def sold_options(api, message):
    if message["name"] == "sold-options":
        api.sold_options_respond = message
        if hasattr(api, 'sold_options_respond_event'):
            api.sold_options_respond_event.set()
