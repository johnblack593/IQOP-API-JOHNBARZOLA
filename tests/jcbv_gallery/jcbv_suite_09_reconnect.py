import unittest
from unittest.mock import patch
import time

from iqoptionapi.reconnect import ReconnectManager, MaxReconnectAttemptsError

class TestReconnectManager(unittest.TestCase):

    def setUp(self):
        self.rm = ReconnectManager(base=2, cap=10, max_attempts=3)

    @patch('iqoptionapi.reconnect.time.sleep')
    @patch('iqoptionapi.reconnect.random.random', return_value=0.5) # Zero jitter
    def test_reconnect_wait_increases_exponentially(self, mock_random, mock_sleep):
        self.rm.wait()
        mock_sleep.assert_called_with(2.0) # 2^1 = 2
        
        self.rm.wait()
        mock_sleep.assert_called_with(4.0) # 2^2 = 4
        
        self.rm.wait()
        mock_sleep.assert_called_with(8.0) # 2^3 = 8
        
        self.assertEqual(mock_sleep.call_count, 3)
        self.assertEqual(self.rm.attempts, 3)

    @patch('iqoptionapi.reconnect.time.sleep')
    def test_max_attempts_exhausted(self, mock_sleep):
        self.rm.wait()
        self.rm.wait()
        self.rm.wait()
        
        with self.assertRaises(MaxReconnectAttemptsError):
            self.rm.wait()  # Attempt 4 should raise

    @patch('iqoptionapi.reconnect.time.sleep')
    def test_wait_never_exceeds_cap(self, mock_sleep):
        # Even with max attempts high, wait time should cap at 10
        rm_capped = ReconnectManager(base=2, cap=10, max_attempts=10)
        
        times = []
        def append_sleep(x):
            times.append(x)
        mock_sleep.side_effect = append_sleep
        
        for _ in range(5):
            rm_capped.wait()
            
        for t in times:
            # We must account for jitter in the real logic
            # Jitter is max +/- 0.5 * raw_wait
            self.assertTrue(t <= 15.0)  # max wait = 10, max jitter = +5
            
    @patch('iqoptionapi.reconnect.time.sleep')
    def test_reset(self, mock_sleep):
        self.rm.wait()
        self.assertEqual(self.rm.attempts, 1)
        self.rm.reset()
        self.assertEqual(self.rm.attempts, 0)
        
    @patch('iqoptionapi.reconnect.time.sleep')
    @patch('iqoptionapi.reconnect.random.random')
    def test_jitter_range(self, mock_random, mock_sleep):
        # random() = 1.0 -> 2*random() - 1 = 1.0 -> jitter = 0.5 * raw_wait 
        mock_random.return_value = 1.0
        self.rm.wait()
        mock_sleep.assert_called_with(3.0)  # 2 + 1.0

        # random() = 0.0 -> 2*random() - 1 = -1.0 -> jitter = -0.5 * raw_wait
        self.rm.reset()
        mock_random.return_value = 0.0
        self.rm.wait()
        mock_sleep.assert_called_with(1.0)  # 2 - 1.0

if __name__ == '__main__':
    unittest.main()
