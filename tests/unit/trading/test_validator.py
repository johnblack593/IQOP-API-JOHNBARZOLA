import pytest
import math
from iqoptionapi.validator import (
    validate_amount, validate_action, validate_candle_size,
    validate_duration, validate_active, validate_sl_tp,
    TradingValidationError
)


class TestValidateAmount:
    def test_valid_amount(self):
        """validate_amount(10.0) no lanza excepción"""
        validate_amount(10.0)
        validate_amount(1)

    def test_zero_raises(self):
        """validate_amount(0) lanza TradingValidationError"""
        with pytest.raises(TradingValidationError, match="es menor al mínimo permitido"):
            validate_amount(0)

    def test_negative_raises(self):
        """validate_amount(-5.0) lanza TradingValidationError"""
        with pytest.raises(TradingValidationError, match="es menor al mínimo permitido"):
            validate_amount(-5.0)

    def test_below_minimum_raises(self):
        """validate_amount(0.5, min_amount=1.0) lanza"""
        with pytest.raises(TradingValidationError, match="es menor al mínimo permitido"):
            validate_amount(0.5, min_amount=1.0)

    def test_nan_raises(self):
        """validate_amount(float('nan')) lanza TradingValidationError"""
        with pytest.raises(TradingValidationError, match="no puede ser NaN ni infinito"):
            validate_amount(float('nan'))

    def test_inf_raises(self):
        """validate_amount(float('inf')) lanza TradingValidationError"""
        with pytest.raises(TradingValidationError, match="no puede ser NaN ni infinito"):
            validate_amount(float('inf'))

    def test_string_raises(self):
        """validate_amount("10") lanza TradingValidationError"""
        with pytest.raises(TradingValidationError, match="debe ser numérico"):
            validate_amount("10")

    def test_error_has_param(self):
        """la excepción tiene .param == "amount" """
        with pytest.raises(TradingValidationError) as excinfo:
            validate_amount("abc")
        assert excinfo.value.param == "amount"


class TestValidateAction:
    def test_call_aliases(self):
        """'call', 'Call', 'CALL', 'buy', 'C' → retorna 'call'"""
        for a in ["call", "Call", "CALL", "buy", "C", "c"]:
            assert validate_action(a) == "call"

    def test_put_aliases(self):
        """'put', 'Put', 'PUT', 'sell', 'P' → retorna 'put'"""
        for a in ["put", "Put", "PUT", "sell", "P", "p"]:
            assert validate_action(a) == "put"

    def test_invalid_raises(self):
        """'hold', 'long', 'x' lanza TradingValidationError"""
        with pytest.raises(TradingValidationError, match="no válido"):
            validate_action("hold")

    def test_error_has_param(self):
        """ .param == "action" """
        with pytest.raises(TradingValidationError) as excinfo:
            validate_action("unknown")
        assert excinfo.value.param == "action"


class TestValidateCandleSize:
    def test_valid_sizes(self):
        """1, 60, 3600, 86400 no lanzan excepción"""
        for s in [1, 60, 3600, 86400]:
            validate_candle_size(s)

    def test_invalid_size_raises(self):
        """2, 7, 45, 999 lanzan TradingValidationError"""
        with pytest.raises(TradingValidationError, match="no soportado"):
            validate_candle_size(2)

    def test_error_has_param(self):
        """ .param == "size" """
        with pytest.raises(TradingValidationError) as excinfo:
            validate_candle_size(2)
        assert excinfo.value.param == "size"


class TestValidateDuration:
    def test_binary_valid(self):
        """1..5 con option_type="binary" no lanzan"""
        for d in range(1, 6):
            validate_duration(d, "binary")
            validate_duration(d, "turbo")

    def test_binary_invalid(self):
        """6, 10, 0 con option_type="binary" lanzan"""
        with pytest.raises(TradingValidationError, match="no válido para binary"):
            validate_duration(6, "binary")

    def test_digital_valid(self):
        """1..5 con option_type="digital" no lanzan"""
        for d in range(1, 6):
            validate_duration(d, "digital")

    def test_blitz_valid(self):
        """5, 10, 15, 20, 30, 45 con option_type="blitz" no lanzan"""
        for d in [5, 10, 15, 20, 30, 45]:
            validate_duration(d, "blitz")

    def test_blitz_invalid(self):
        """1, 60, 3 con option_type="blitz" lanzan"""
        with pytest.raises(TradingValidationError, match="no válido para blitz"):
            validate_duration(1, "blitz")

    def test_unknown_type_raises(self):
        """option_type="exotic" lanza TradingValidationError"""
        with pytest.raises(TradingValidationError, match="no reconocido"):
            validate_duration(1, "exotic")


class TestValidateActive:
    def test_valid_active(self):
        """'EURUSD' en {'EURUSD': 1} no lanza"""
        validate_active("EURUSD", {"EURUSD": 1})

    def test_invalid_raises(self):
        """'XYZABC' no en actives_map lanza TradingValidationError"""
        with pytest.raises(TradingValidationError, match="no encontrado"):
            validate_active("XYZABC", {"EURUSD": 1})

    def test_suggestion_in_message(self):
        """'eurusd' en {'EURUSD': 1} — el mensaje de error contiene sugerencia"""
        with pytest.raises(TradingValidationError, match="¿Quisiste decir"):
            validate_active("eurusd", {"EURUSD": 1})

    def test_error_has_param(self):
        """ .param == "active" """
        with pytest.raises(TradingValidationError) as excinfo:
            validate_active("XYZ", {})
        assert excinfo.value.param == "active"


class TestValidateSlTp:
    def test_both_none_valid(self):
        """(None, None, None, None) no lanza"""
        validate_sl_tp(None, None, None, None)

    def test_valid_percent(self):
        """('percent', 50.0, 'percent', 100.0) no lanza"""
        validate_sl_tp("percent", 50.0, "percent", 100.0)

    def test_valid_price(self):
        """('price', 1.0800, None, None) no lanza"""
        validate_sl_tp("price", 1.08, None, None)

    def test_invalid_kind_raises(self):
        """('pips', 5.0, None, None) lanza"""
        with pytest.raises(TradingValidationError, match="no válido"):
            validate_sl_tp("pips", 5.0, None, None)

    def test_kind_set_value_none_raises(self):
        """('percent', None, None, None) lanza"""
        with pytest.raises(TradingValidationError, match="debe ser > 0"):
            validate_sl_tp("percent", None, None, None)

    def test_kind_set_value_zero_raises(self):
        """('price', 0.0, None, None) lanza"""
        with pytest.raises(TradingValidationError, match="debe ser > 0"):
            validate_sl_tp("price", 0.0, None, None)

    def test_error_has_param(self):
        """ .param comienza con 'stop_lose' o 'take_profit' """
        with pytest.raises(TradingValidationError) as excinfo:
            validate_sl_tp("invalid", 10.0, None, None)
        assert excinfo.value.param == "stop_lose_kind"
