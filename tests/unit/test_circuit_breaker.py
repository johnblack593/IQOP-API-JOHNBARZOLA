import unittest
import time
from iqoptionapi.circuit_breaker import CircuitBreaker, CircuitBreakerState

class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.cb = CircuitBreaker(
            max_consecutive_losses=3,
            max_session_loss_usd=10.0,
            max_drawdown_pct=0.10,
            recovery_wait_secs=0.1 # Very short for testing
        )
        self.cb.reset_session(100.0)

    def test_initial_state_is_closed(self):
        self.assertEqual(self.cb.state, CircuitBreakerState.CLOSED)
        self.assertTrue(self.cb.can_trade())

    def test_consecutive_losses_triggers_open(self):
        self.cb.record_loss(1.0, 99.0)
        self.cb.record_loss(1.0, 98.0)
        self.assertEqual(self.cb.state, CircuitBreakerState.CLOSED)
        self.cb.record_loss(1.0, 97.0)
        self.assertEqual(self.cb.state, CircuitBreakerState.OPEN)
        self.assertFalse(self.cb.can_trade())

    def test_session_loss_triggers_open(self):
        self.cb.record_loss(11.0, 89.0)
        self.assertEqual(self.cb.state, CircuitBreakerState.OPEN)

    def test_drawdown_triggers_open(self):
        # 10% of 100 is 10.0
        self.cb.record_loss(10.5, 89.5)
        self.assertEqual(self.cb.state, CircuitBreakerState.OPEN)

    def test_open_blocks_trading(self):
        self.cb.record_loss(15.0, 85.0)
        self.assertFalse(self.cb.can_trade())

    def test_recovery_to_half_after_wait(self):
        self.cb.record_loss(15.0, 85.0)
        self.assertEqual(self.cb.state, CircuitBreakerState.OPEN)
        time.sleep(0.15)
        self.assertEqual(self.cb.state, CircuitBreakerState.HALF)
        self.assertTrue(self.cb.can_trade())

    def test_half_win_closes_circuit(self):
        self.cb.record_loss(15.0, 85.0)
        time.sleep(0.15)
        self.assertEqual(self.cb.state, CircuitBreakerState.HALF)
        self.cb.record_win(1.0, 86.0)
        self.assertEqual(self.cb.state, CircuitBreakerState.CLOSED)

    def test_half_loss_reopens_circuit(self):
        self.cb.record_loss(15.0, 85.0)
        time.sleep(0.15)
        self.assertEqual(self.cb.state, CircuitBreakerState.HALF)
        self.cb.record_loss(1.0, 84.0)
        self.assertEqual(self.cb.state, CircuitBreakerState.OPEN)

    def test_win_resets_consecutive_losses(self):
        self.cb.record_loss(1.0, 99.0)
        self.cb.record_loss(1.0, 98.0)
        self.cb.record_win(1.0, 99.0)
        self.assertEqual(self.cb.consecutive_losses, 0)
        self.cb.record_loss(1.0, 98.0)
        self.assertEqual(self.cb.state, CircuitBreakerState.CLOSED)

    def test_reset_session_clears_metrics(self):
        self.cb.record_loss(5.0, 95.0)
        self.cb.reset_session(200.0)
        self.assertEqual(self.cb.session_loss_usd, 0.0)
        self.assertEqual(self.cb.consecutive_losses, 0)
        self.assertEqual(self.cb.state, CircuitBreakerState.CLOSED)

    def test_trips_today_increments_on_trip(self):
        self.assertEqual(self.cb.trips_today, 0)
        self.cb.record_loss(15.0, 85.0)
        self.assertEqual(self.cb.trips_today, 1)

if __name__ == '__main__':
    unittest.main()
