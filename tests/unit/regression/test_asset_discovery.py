import unittest
from unittest.mock import MagicMock, patch
from iqoptionapi.stable_api import IQ_Option

class TestAssetDiscoveryRegression(unittest.TestCase):
    """
    Regression tests for asset discovery and catalog population.
    """

    def setUp(self):
        with patch('iqoptionapi.stable_api.IQ_Option.connect', return_value=(True, None)):
            self.iq = IQ_Option("test@example.com", "password")
            self.iq.api = MagicMock()

    def test_get_all_open_time_structure(self):
        """Verify that get_all_open_time handles empty/missing data gracefully (Sprint 2 fix)"""
        # Mock get_all_init to return None (the case that caused the error)
        self.iq.get_all_init = MagicMock(return_value=None)
        self.iq.get_all_init_v2 = MagicMock(return_value=None)
        
        # This should NOT raise NoneType error anymore
        try:
            data = self.iq.get_all_open_time()
            self.assertIsInstance(data, dict)
        except Exception as e:
            self.fail(f"get_all_open_time raised {type(e).__name__}: {e}")

    def test_instruments_population(self):
        """Verify that instruments are correctly added to constants.ACTIVES"""
        import iqoptionapi.core.constants as OP_code
        OP_code.ACTIVES = {}
        
        mock_instruments = {
            "instruments": [
                {"id": "EURUSD", "active_id": 1},
                {"id": "BTCUSD", "active_id": 2}
            ]
        }
        
        self.iq.get_instruments = MagicMock(return_value=mock_instruments)
        self.iq.instruments_input_to_ACTIVES("forex")
        
        self.assertEqual(OP_code.ACTIVES.get("EURUSD"), 1)
        self.assertEqual(OP_code.ACTIVES.get("BTCUSD"), 2)

if __name__ == "__main__":
    unittest.main()

