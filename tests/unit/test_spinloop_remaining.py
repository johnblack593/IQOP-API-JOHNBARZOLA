import unittest
from unittest.mock import MagicMock, patch
import threading
from iqoptionapi.stable_api import IQ_Option

class TestSpinloopElimination(unittest.TestCase):
    def setUp(self):
        self.api = IQ_Option("email", "password")
        self.api.api = MagicMock()
        # Mock timesync for expiration calculations
        self.api.api.timesync.server_timestamp = 1600000000

    @patch('time.sleep')
    def test_get_all_init_v2_no_sleep(self, mock_sleep):
        """Verify get_all_init_v2 uses Event.wait and not time.sleep when data is ready."""
        self.api.api.api_option_init_all_result_v2 = None
        
        def side_effect():
            self.api.api.api_option_init_all_result_v2 = {"status": "ok"}
            self.api.api.api_option_init_all_result_v2_event.set()
            
        self.api.api.get_api_option_init_all_v2.side_effect = side_effect
        
        res = self.api.get_all_init_v2()
        
        self.assertEqual(res, {"status": "ok"})
        mock_sleep.assert_not_called()
        self.api.api.get_api_option_init_all_v2.assert_called_once()

    @patch('time.sleep')
    def test_get_profile_async_no_sleep(self, mock_sleep):
        """Verify get_profile_ansyc uses Event.wait."""
        self.api.api.profile.msg = {"name": "test"}
        self.api.api.profile_event.set()
        
        res = self.api.get_profile_ansyc()
        
        self.assertEqual(res, {"name": "test"})
        mock_sleep.assert_not_called()

    @patch('time.sleep')
    def test_buy_no_sleep(self, mock_sleep):
        """Verify buy uses Event.wait."""
        self.api.api.result = True
        req_id = None
        
        # We need to capture the req_id passed to buyv3
        def side_effect(*args, **kwargs):
            nonlocal req_id
            req_id = args[4]
            self.api.api.buy_multi_option[req_id] = {"id": 12345}
            self.api.api.result_event.set()

        self.api.api.buyv3.side_effect = side_effect
        
        check, id = self.api.buy(1, "EURUSD", "call", 1)
        
        self.assertTrue(check)
        self.assertEqual(id, 12345)
        mock_sleep.assert_not_called()

    @patch('time.sleep')
    def test_buy_digital_spot_no_sleep(self, mock_sleep):
        """Verify buy_digital_spot uses Event.wait."""
        # Mock get_expiration_time
        with patch('iqoptionapi.expiration.get_expiration_time', return_value=(1600000000, 1)):
            def side_effect(instrument_id, active_id, amount):
                # Simulate WS response
                # We need to know the request_id returned by place_digital_option
                # But place_digital_option in stable_api is called and its return is used
                return "req_123"

            self.api.api.place_digital_option_v2.side_effect = side_effect
            
            # Pre-set the result in the dict
            self.api.api.digital_option_placed_id = {"req_123": 999}
            self.api.api.digital_option_placed_id_event.set()
            
            check, id = self.api.buy_digital_spot("EURUSD", 1, "call", 1)
            
            self.assertTrue(check)
            self.assertEqual(id, 999)
            mock_sleep.assert_not_called()

if __name__ == '__main__':
    unittest.main()
