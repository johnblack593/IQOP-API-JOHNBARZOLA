import unittest
from datetime import datetime, timezone
from iqoptionapi.session_scheduler import SessionScheduler, MarketSession

class TestSessionScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = SessionScheduler()

    def test_london_session_detected(self):
        # 10:00 UTC is London
        dt = datetime(2023, 10, 18, 10, 0, tzinfo=timezone.utc)
        sessions = self.scheduler.current_sessions(dt)
        self.assertIn(MarketSession.LONDON, sessions)

    def test_new_york_session_detected(self):
        # 14:00 UTC is London + NY Overlap
        dt = datetime(2023, 10, 18, 14, 0, tzinfo=timezone.utc)
        sessions = self.scheduler.current_sessions(dt)
        self.assertIn(MarketSession.NEW_YORK, sessions)
        self.assertIn(MarketSession.OVERLAP_LONDON_NY, sessions)

    def test_weekend_returns_closed(self):
        # Saturday
        dt = datetime(2023, 10, 21, 10, 0, tzinfo=timezone.utc)
        sessions = self.scheduler.current_sessions(dt)
        self.assertEqual(sessions, [MarketSession.CLOSED])
        self.assertFalse(self.scheduler.is_trading_time(dt=dt))

    def test_blocked_hours_respected(self):
        sched = SessionScheduler(blocked_hours_utc=[10])
        dt = datetime(2023, 10, 18, 10, 0, tzinfo=timezone.utc)
        self.assertFalse(sched.is_trading_time(dt=dt))

    def test_allowed_sessions_filter(self):
        # 10:00 is London. If we only allow NY:
        sched = SessionScheduler(allowed_sessions=[MarketSession.NEW_YORK])
        dt = datetime(2023, 10, 18, 10, 0, tzinfo=timezone.utc)
        self.assertFalse(sched.is_trading_time(dt=dt))

    def test_is_trading_time_true_in_session(self):
        dt = datetime(2023, 10, 18, 10, 0, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_trading_time(dt=dt))

if __name__ == '__main__':
    unittest.main()
