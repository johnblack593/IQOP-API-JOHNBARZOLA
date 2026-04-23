"""Module for IQ option websocket — portfolio.get-positions handler."""

from iqoptionapi.ws.objects.portfolio_positions import PortfolioPositions


def portfolio_get_positions(api, message):
    if message.get("name") == "portfolio.get-positions":
        PortfolioPositions.handle(api, message)
