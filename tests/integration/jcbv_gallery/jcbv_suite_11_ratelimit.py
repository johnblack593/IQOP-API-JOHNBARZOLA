import unittest
from unittest.mock import patch

from iqoptionapi.core.ratelimit import TokenBucket, RateLimitExceededError


class TestTokenBucket(unittest.TestCase):

    def test_consume_available_tokens_succeeds(self):
        bucket = TokenBucket(capacity=3.0, refill_rate=1.0, block=False)
        # Should not raise for 3 consecutive calls
        bucket.consume()
        bucket.consume()
        bucket.consume()

    def test_consume_beyond_capacity_raises(self):
        bucket = TokenBucket(capacity=2.0, refill_rate=0.1, block=False)
        bucket.consume()
        bucket.consume()
        with self.assertRaises(RateLimitExceededError):
            bucket.consume()

    @patch('iqoptionapi.ratelimit.time.monotonic')
    def test_tokens_replenish_after_wait(self, mock_monotonic):
        mock_monotonic.return_value = 1000.0
        bucket = TokenBucket(capacity=2.0, refill_rate=1.0, block=False)

        # Consume both tokens
        bucket.consume()
        bucket.consume()

        # Advance time by 1 second → should refill 1 token
        mock_monotonic.return_value = 1001.0
        bucket.consume()  # should succeed

    @patch('iqoptionapi.ratelimit.time.sleep')
    @patch('iqoptionapi.ratelimit.time.monotonic')
    def test_block_mode_waits(self, mock_monotonic, mock_sleep):
        mock_monotonic.return_value = 1000.0
        bucket = TokenBucket(capacity=1.0, refill_rate=1.0, block=True)
        bucket.consume()

        # Next consume should block (sleep), not raise
        # After sleep mock returns, advance time so refill works
        def advance_time(wait_time):
            mock_monotonic.return_value = mock_monotonic.return_value + wait_time

        mock_sleep.side_effect = advance_time
        bucket.consume()  # should NOT raise
        mock_sleep.assert_called()

    def test_available_tokens_returns_float(self):
        bucket = TokenBucket(capacity=5.0, refill_rate=0.5, block=False)
        tokens = bucket.available_tokens
        self.assertIsInstance(tokens, float)
        self.assertGreaterEqual(tokens, 0.0)
        self.assertLessEqual(tokens, 5.0)


if __name__ == '__main__':
    unittest.main()

