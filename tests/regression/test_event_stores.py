import unittest
import threading
from unittest.mock import MagicMock, patch
from collections import defaultdict
from iqoptionapi.stable_api import IQ_Option

class TestEventStoresRegression(unittest.TestCase):
    """
    Regression tests for Event Store management and _wait_result logic.
    These tests use mocks to avoid real network connections.
    """

    def setUp(self):
        # Patch connect to avoid real network
        with patch('iqoptionapi.stable_api.IQ_Option.connect', return_value=(True, None)):
            self.iq = IQ_Option("test@example.com", "password")
            # Manually mock the API object since connect is patched
            self.iq.api = MagicMock()
            self.iq.api.result_event_store = defaultdict(threading.Event)
            self.iq.api.socket_option_closed_event = defaultdict(threading.Event)

    def test_wait_result_cleanup(self):
        """Verify that _wait_result cleans up the event store after success"""
        order_id = 12345
        event = self.iq.api.result_event_store[order_id]
        
        # Simulate result arriving
        mock_store = {order_id: {"status": "win"}}
        
        # We need to signal the event in a separate thread or just before calling wait
        event.set()
        
        result = self.iq._wait_result(
            order_id=order_id,
            result_store=mock_store,
            event_store=self.iq.api.result_event_store,
            timeout=1.0
        )
        
        self.assertEqual(result["status"], "win")
        # S1-T6: Event should be removed from store
        self.assertNotIn(order_id, self.iq.api.result_event_store)

    def test_wait_result_timeout(self):
        """Verify that _wait_result cleans up even on timeout"""
        order_id = 99999
        # Do NOT set the event
        
        result = self.iq._wait_result(
            order_id=order_id,
            result_store={},
            event_store=self.iq.api.result_event_store,
            timeout=0.1
        )
        
        self.assertIsNone(result)
        # Should still be cleaned up to prevent leaks
        self.assertNotIn(order_id, self.iq.api.result_event_store)

if __name__ == "__main__":
    unittest.main()
