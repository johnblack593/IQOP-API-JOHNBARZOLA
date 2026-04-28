
from iqoptionapi.ws.channels.base import Base


class Get_instruments(Base):
    """Class for IQ option buy websocket chanel."""
    # pylint: disable=too-few-public-methods

    name = "sendMessage"

    def __call__(self,types):
        # New API routing: convert legacy 'types' to category-specific underlying-list endpoint
        api_type = types
        if types == "crypto":
            api_type = "marginal-crypto-instruments"
        elif types == "forex":
            api_type = "marginal-forex-instruments"
        elif types in ["cfd", "stocks", "indices", "commodities", "etf"]:
            api_type = "marginal-cfd-instruments"
        elif types == "digital-option":
            api_type = "digital-option-instruments"

        name_str = f"{api_type}.get-underlying-list"
        
        # Digital options use v3.0 with filter_suspended, margin uses v1.0 with empty body
        version = "3.0" if types == "digital-option" else "1.0"
        body = {"filter_suspended": True} if types == "digital-option" else {}

        data = {
            "name": name_str,
            "version": version,
            "body": body
        }

        self.send_websocket_request(self.name, data)
