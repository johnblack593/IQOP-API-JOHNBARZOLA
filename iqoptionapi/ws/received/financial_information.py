"""Module for IQ option websocket."""

def financial_information(api, message):
    if message["name"] == "financial-information":
            api.financial_information = message
            if hasattr(api, 'financial_information_event'):
                api.financial_information_event.set()