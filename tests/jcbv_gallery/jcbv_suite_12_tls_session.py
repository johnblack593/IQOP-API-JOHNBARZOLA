import unittest
from unittest.mock import patch, MagicMock
import certifi

from iqoptionapi.http import session as session_module
from iqoptionapi.http.session import get_shared_session, close_shared_session


class TestTLSSession(unittest.TestCase):

    def setUp(self):
        # Ensure clean state before each test
        close_shared_session()

    def tearDown(self):
        close_shared_session()

    def test_get_shared_session_returns_session(self):
        import requests
        s = get_shared_session()
        self.assertIsInstance(s, requests.Session)

    def test_session_verify_equals_certifi_where(self):
        s = get_shared_session()
        self.assertEqual(s.verify, certifi.where())

    def test_singleton_behavior(self):
        s1 = get_shared_session()
        s2 = get_shared_session()
        self.assertIs(s1, s2)

    def test_close_sets_none(self):
        get_shared_session()
        close_shared_session()
        self.assertIsNone(session_module._shared_session)

    def test_fresh_session_after_close(self):
        s1 = get_shared_session()
        close_shared_session()
        s2 = get_shared_session()
        self.assertIsNot(s1, s2)


if __name__ == '__main__':
    unittest.main()
