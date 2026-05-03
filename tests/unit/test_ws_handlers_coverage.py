"""
tests/unit/test_ws_handlers_coverage.py
───────────────────────────────────────
Tests para los handlers de mensajes recibidos por websocket.
"""
import pytest
from unittest.mock import MagicMock
from iqoptionapi.ws.received.auth.balance import balances
from iqoptionapi.ws.received.auth.heartbeat import heartbeat
from iqoptionapi.ws.received.market.candles import candles
from iqoptionapi.ws.received.orders.order_placed_temp import order_placed_temp
from iqoptionapi.ws.received.market.traders_mood_changed import traders_mood_changed

class TestWSHandlers:
    def test_balance_handler(self):
        api = MagicMock()
        msg = {"name": "balances", "msg": {"amount": 1000, "id": 123}}
        balances(api, msg)
        assert api.balances_raw == msg

    def test_heartbeat_handler(self):
        api = MagicMock()
        # Mock heartbeat as a callable since the handler calls it
        api.heartbeat = MagicMock()
        msg = {"name": "heartbeat", "msg": 123456789}
        heartbeat(api, msg)
        api.heartbeat.assert_called_with(123456789)

    def test_candles_handler(self):
        api = MagicMock()
        api.candles = MagicMock()
        msg = {"name": "candles", "msg": {"candles": [{"from": 1, "close": 1.1}]}}
        candles(api, msg)
        assert api.candles.candles_data == [{"from": 1, "close": 1.1}]
        api.candles_event.set.assert_called_once()

    def test_order_placed_temp_handler(self):
        api = MagicMock()
        msg = {"name": "order-placed-temp", "msg": {"id": 999, "request_id": "req1"}}
        order_placed_temp(api, msg)
        assert api.buy_order_id == 999
        api.order_data_event.set.assert_called_once()

    def test_traders_mood_changed_handler(self):
        api = MagicMock()
        api.traders_mood = {}
        msg = {"name": "traders-mood-changed", "msg": {"asset_id": 1, "value": 0.5}}
        traders_mood_changed(api, msg)
        assert api.traders_mood[1] == 0.5
