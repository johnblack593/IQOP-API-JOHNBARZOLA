import pytest
from unittest.mock import MagicMock, patch
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.ratelimit import TokenBucket


class TestBuyGuardRateLimit:
    @pytest.fixture
    def iq(self):
        # Email/password ficticios
        iq = IQ_Option("test@example.com", "password")
        # Simular la API sin conexión real
        iq.api = MagicMock()
        # Forzar agotamiento inmediato del rate limiter
        # capacity=0.0 hará que cualquier consume() falle si refill es lento
        iq._rate_limiter = TokenBucket(capacity=0.0, refill_rate=0.001, block=False)
        return iq

    def test_buy_blocked_returns_false_none(self, iq):
        """retorna (False, None) y NO llama a self.api.buyv3 cuando está bloqueado"""
        result = iq.buy(10.0, "EURUSD", "call", 1)
        assert result == (False, None)
        assert not iq.api.buyv3.called

    def test_buy_order_blocked_returns_false_none(self, iq):
        """retorna (False, None) y NO llama a self.api.buy_order cuando está bloqueado"""
        # buy_order tiene validaciones previas, pero el rate limit está antes de la llamada final
        # En la implementación actual de stable_api.py, buy_order retorna (False, None)
        result = iq.buy_order(
            instrument_type="forex", instrument_id="EURUSD",
            side="buy", amount=1, leverage=1, type="market"
        )
        assert result == (False, None)
        assert not iq.api.buy_order.called

    def test_buy_digital_spot_blocked_returns_false_none(self, iq):
        """retorna (False, None) y NO llama a self.api.place_digital_option cuando está bloqueado"""
        result = iq.buy_digital_spot("EURUSD", 10.0, "call", 1)
        assert result == (False, None)
        assert not iq.api.place_digital_option.called

    def test_buy_digital_spot_v2_blocked_returns_false_none(self, iq):
        """retorna (False, None) y NO llama a self.api.place_digital_option cuando está bloqueado"""
        result = iq.buy_digital_spot_v2("EURUSD", 10.0, "call", 1)
        assert result == (False, None)
        assert not iq.api.place_digital_option.called

    def test_sell_option_blocked_returns_none(self, iq):
        """retorna None y NO llama a self.api.sell_option cuando está bloqueado"""
        result = iq.sell_option([123])
        assert result is None
        assert not iq.api.sell_option.called

    def test_sell_digital_option_blocked_returns_none(self, iq):
        """retorna None y NO llama a self.api.sell_digital_option cuando está bloqueado"""
        result = iq.sell_digital_option([123])
        assert result is None
        assert not iq.api.sell_digital_option.called

    def test_close_position_blocked_returns_false(self, iq):
        """retorna False y NO llama a self.api.close_position cuando está bloqueado"""
        # Nota: close_position llama a get_order primero en la implementación actual, 
        # pero con el rate limiter al inicio debería fallar antes.
        result = iq.close_position(123)
        assert result is False
        assert not iq.api.get_order.called

    def test_rate_limiter_allows_after_refill(self):
        """Con rate limiter con 1 token, la primera llamada pasa, la segunda falla"""
        iq = IQ_Option("test@example.com", "password")
        iq.api = MagicMock()
        # 1 token disponible, refill muy lento
        iq._rate_limiter = TokenBucket(capacity=1.0, refill_rate=0.0001, block=False)
        
        # Primera llamada - OK
        # Simular que buyv3 retorna algo para que no falle el resto del método buy()
        # Aunque buy() no retorna el resultado de buyv3 directamente sino que espera eventos.
        # Pero aquí solo nos importa si se llamó.
        iq.buy(10.0, "EURUSD", "call", 1)
        assert iq.api.buyv3.called
        
        # Segunda llamada - Bloqueada
        result = iq.buy(10.0, "EURUSD", "call", 1)
        assert result == (False, None)
        assert iq.api.buyv3.call_count == 1
