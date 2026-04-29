import pytest
from unittest.mock import MagicMock

class TestBinary:
    def test_buy_returns_tuple(self, mock_iq):
        def mock_buyv3(amount, active, action, exp, req_id):
            mock_iq.api.buy_multi_option[req_id] = {"id": "12345"}
        mock_iq.api.buyv3.side_effect = mock_buyv3
        mock_iq.api.result = True
        res = mock_iq.buy(1, "EURUSD", "call", 1)
        assert isinstance(res, tuple)
        assert res[1] == "12345"

    def test_buy_with_invalid_amount_returns_false(self, mock_iq):
        # El validador lanzaría TradingValidationError si lo llamamos, 
        # pero aquí probamos el retorno de la lógica si falla
        res = mock_iq.buy(-1, "EURUSD", "call", 1)
        assert res[0] is False

    def test_buy_respects_rate_limit(self, mock_iq):
        mock_iq._order_bucket.consume.return_value = True
        mock_iq.buy(1, "EURUSD", "call", 1)
        mock_iq._order_bucket.consume.assert_called()

    def test_sell_option_returns_tuple(self, mock_iq):
        mock_iq.api.result = (True, {"status": "ok"})
        mock_iq.api.sell_option.side_effect = lambda ids: mock_iq.api.result_event.set()
        res = mock_iq.sell_option("id_123")
        assert res[0] is True

class TestDigital:
    def test_buy_digital_spot_call(self, mock_iq):
        def mock_place_v2(inst, active, amount):
            mock_iq.api.digital_option_placed_id = {"test_req": 12345}
            mock_iq.api.digital_option_placed_id_event.set()
            return "test_req"
        mock_iq.api.place_digital_option_v2.side_effect = mock_place_v2
        res = mock_iq.buy_digital_spot("EURUSD", 1, "call", 1)
        assert res[0] is True
        assert res[1] == 12345

    def test_buy_digital_spot_put(self, mock_iq):
        def mock_place_v2(inst, active, amount):
            mock_iq.api.digital_option_placed_id = {"test_req": 12345}
            mock_iq.api.digital_option_placed_id_event.set()
            return "test_req"
        mock_iq.api.place_digital_option_v2.side_effect = mock_place_v2
        res = mock_iq.buy_digital_spot("EURUSD", 1, "put", 1)
        assert res[0] is True

    def test_sell_digital_option(self, mock_iq):
        mock_iq.api.result = (True, "ok")
        mock_iq.api.sell_digital_option.side_effect = lambda id: mock_iq.api.result_event.set()
        res = mock_iq.sell_digital_option("id_dig")
        assert res[0] is True

    def test_buy_digital_invalid_direction_raises(self, mock_iq):
        from iqoptionapi.validator import TradingValidationError
        # Simular que el validador real detecta el error
        mock_iq.validator.validate_order.side_effect = TradingValidationError("invalid")
        with pytest.raises(TradingValidationError):
            mock_iq.buy_digital_spot("EURUSD", 1, "invalid", 1)

class TestMargin:
    def test_buy_order_creates_position(self, mock_iq):
        def mock_buy_order(**kwargs):
            mock_iq.api.buy_order_id = "pos_id"
        mock_iq.api.buy_order.side_effect = mock_buy_order
        res = mock_iq.buy_order("forex", "EURUSD", "buy", 1, 100)
        assert res[0] is True
        assert res[1] == "pos_id"

    def test_close_position_calls_api(self, mock_iq):
        mock_iq.api.close_position_data = {"status": 2000}
        # Simular que el thread de WS setea el evento al recibir comando
        mock_iq.api.close_position.side_effect = lambda pid: mock_iq.api.close_position_event.set()
        res = mock_iq.close_position("pos_id")
        assert res is True

class TestRateLimit:
    def test_rate_limit_exceeded_returns_false_none(self, mock_iq):
        from iqoptionapi.core.ratelimit import RateLimitExceededError
        mock_iq._order_bucket.consume.side_effect = RateLimitExceededError("limit")
        res = mock_iq.buy(1, "EURUSD", "call", 1)
        # buy() captura RateLimitExceededError y retorna (False, None)
        assert res == (False, None)

    def test_rate_limit_bucket_consumed_on_buy(self, mock_iq):
        mock_iq.buy(1, "EURUSD", "call", 1)
        mock_iq._order_bucket.consume.assert_called_once()
