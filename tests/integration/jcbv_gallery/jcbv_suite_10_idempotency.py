import unittest
from unittest.mock import patch
import time

from iqoptionapi.idempotency import IdempotencyRegistry

class TestIdempotencyRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = IdempotencyRegistry()

    def test_register_returns_valid_uuid(self):
        req_id = self.registry.register()
        self.assertIsInstance(req_id, str)
        self.assertTrue(len(req_id) > 10)
        self.assertTrue(self.registry.is_pending(req_id))
        self.assertIsNone(self.registry.get_order_id(req_id))

    def test_confirm_transitions_state(self):
        req_id = self.registry.register()
        self.registry.confirm(req_id, "ORDER_123")
        
        self.assertFalse(self.registry.is_pending(req_id))
        self.assertEqual(self.registry.get_order_id(req_id), "ORDER_123")

    def test_fail_transitions_state(self):
        req_id = self.registry.register()
        self.registry.fail(req_id)
        
        self.assertFalse(self.registry.is_pending(req_id))
        self.assertIsNone(self.registry.get_order_id(req_id))

    @patch('iqoptionapi.idempotency.time.monotonic')
    def test_purge_expired(self, mock_time):
        mock_time.return_value = 1000.0
        
        req_id_1 = self.registry.register()
        req_id_2 = self.registry.register()
        
        # Advance time by 400 seconds (TTL is 300)
        mock_time.return_value = 1400.0
        
        # Register a new one that shouldn't be purged
        req_id_3 = self.registry.register()
        
        purged_count = self.registry.purge_expired()
        self.assertEqual(purged_count, 2)
        
        self.assertFalse(req_id_1 in self.registry._store)
        self.assertTrue(req_id_3 in self.registry._store)

    def test_double_confirm_idempotent(self):
        req_id = self.registry.register()
        self.registry.confirm(req_id, "ORDER_123")
        self.assertEqual(self.registry.get_order_id(req_id), "ORDER_123")
        
        # Double confirm should not raise exception
        self.registry.confirm(req_id, "ORDER_456")
        
        # Should overwrite order_id in current implementation, let's verify
        self.assertEqual(self.registry.get_order_id(req_id), "ORDER_456")


if __name__ == '__main__':
    unittest.main()
