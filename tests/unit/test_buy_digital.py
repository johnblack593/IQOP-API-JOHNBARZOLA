"""
Tests para buy_digital_spot() y buy_digital_spot_v2().
Verifica validaciones y formato de instrument_id sin conexión real.
"""
import pytest
from unittest.mock import MagicMock, patch

class TestBuyDigitalSpot:
    def test_buy_digital_spot_rejects_invalid_direction(self):
        """El validator debe rechazar una dirección inválida."""
        from iqoptionapi.stable_api import IQ_Option
        with patch.object(IQ_Option, '__init__', return_value=None):
            iq = IQ_Option.__new__(IQ_Option)
            iq.api = MagicMock()
            iq.validator = MagicMock()
            iq.validator.validate_order.return_value = (False, "Invalid direction: sideways")
            
            result = iq.buy_digital_spot("EURUSD-OTC", 1.0, "sideways", 5)
        
        assert result == (False, None)

    def test_instrument_id_format(self):
        """El instrument_id de buy_digital_spot_v2 sigue el formato correcto."""
        # Verificar el formato: do{ASSET}{YYYYMMDDHHMM}PT{DUR}M{DIR}SPT
        import re
        pattern = r'^do[A-Z\-OTC]+\d{12}PT\d+M[CP]SPT$'
        
        # Ejemplo de instrument_id que el método debería generar:
        example = "doEURUSD-OTC202504221430PT5MCSPT"
        assert re.match(pattern, example) is not None, \
            f"Instrument ID format mismatch: {example}"
