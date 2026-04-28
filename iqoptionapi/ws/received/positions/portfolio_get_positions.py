"""Module for IQ option websocket — portfolio.get-positions handler."""

from iqoptionapi.ws.objects.portfolio_positions import PortfolioPositions


def portfolio_get_positions(api, message):
    name = message.get("name")
    if name in ("portfolio.get-positions", "portfolio.positions", "positions"):
        PortfolioPositions.handle(api, message)
