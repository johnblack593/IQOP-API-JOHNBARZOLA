import pytest
import time
from unittest.mock import patch, MagicMock
from iqoptionapi.core.ratelimit import TokenBucket, RateLimitExceededError
from iqoptionapi.core.config import RATE_LIMIT_CAPACITY, RATE_LIMIT_REFILL


class MockTime:
    def __init__(self, start=1000.0):
        self.now = start
    def __call__(self):
        return self.now
    def advance(self, amount):
        self.now += amount

class TestTokenBucketBasics:
    def test_initial_tokens_full(self):
        """bucket recién creado tiene capacity tokens"""
        bucket = TokenBucket(capacity=5.0, refill_rate=0.5)
        assert bucket.available_tokens == 5.0

    def test_consume_reduces_tokens(self):
        """after consume(), tokens < capacity"""
        bucket = TokenBucket(capacity=5.0, refill_rate=0.5)
        bucket.consume()
        assert bucket.available_tokens == pytest.approx(4.0)

    def test_consume_below_zero_raises(self):
        """cuando tokens=0, consume() lanza RateLimitExceededError"""
        mock_time = MockTime()
        with patch('time.monotonic', side_effect=mock_time):
            bucket = TokenBucket(capacity=1.0, refill_rate=0.5)
            bucket.consume()
            # El tiempo NO avanza → available_tokens debe ser exactamente 0.0
            assert bucket.available_tokens == pytest.approx(0.0)
            with pytest.raises(RateLimitExceededError):
                bucket.consume()

    def test_refill_over_time(self):
        """después de tiempo, tokens se han reabastecido"""
        mock_time = MockTime()
        with patch('time.monotonic', side_effect=mock_time):
            bucket = TokenBucket(capacity=5.0, refill_rate=1.0)
            for _ in range(5):
                bucket.consume()
            assert bucket.available_tokens == pytest.approx(0.0)
            
            mock_time.advance(2.0)
            assert bucket.available_tokens == 2.0

    def test_capacity_not_exceeded_on_refill(self):
        """tokens nunca superan capacity incluso después de largo tiempo"""
        mock_time = MockTime()
        with patch('time.monotonic', side_effect=mock_time):
            bucket = TokenBucket(capacity=5.0, refill_rate=1.0)
            mock_time.advance(100.0)
            assert bucket.available_tokens == 5.0


class TestTokenBucketBlocking:
    def test_block_false_raises_immediately(self):
        """con block=False, lanza RateLimitExceededError inmediatamente si no hay tokens"""
        bucket = TokenBucket(capacity=1.0, refill_rate=0.1, block=False)
        bucket.consume()
        with pytest.raises(RateLimitExceededError):
            bucket.consume()

    @patch('time.sleep', return_value=None)
    def test_block_true_waits(self, mock_sleep):
        """con block=True, consume() bloquea hasta que hay tokens disponibles"""
        mock_time = MockTime()
        # We need monotonic to advance during the loop
        def mock_monotonic():
            val = mock_time.now
            mock_time.advance(0.5) # Advance 0.5s every time it's called
            return val

        with patch('time.monotonic', side_effect=mock_monotonic):
            bucket = TokenBucket(capacity=1.0, refill_rate=1.0, block=True)
            bucket.consume() # tokens 1.0 -> 0.0
            # Next consume will block until tokens >= 1.0
            # tokens will be 0.0, then 0.5, then 1.0
            bucket.consume()
            assert mock_sleep.called


class TestTokenBucketFromConfig:
    def test_defaults_match_config(self):
        """TokenBucket() sin argumentos tiene capacity=RATE_LIMIT_CAPACITY and refill_rate=RATE_LIMIT_REFILL"""
        bucket = TokenBucket()
        assert bucket._capacity == RATE_LIMIT_CAPACITY
        assert bucket._refill_rate == RATE_LIMIT_REFILL

