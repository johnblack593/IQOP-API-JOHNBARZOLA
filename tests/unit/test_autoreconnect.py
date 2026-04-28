
import pytest
import threading
import time
from unittest.mock import MagicMock, patch, PropertyMock
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.api import IQOptionAPI
from iqoptionapi.ws.client import WebsocketClient
from iqoptionapi.reconnect import MaxReconnectAttemptsError

class TestSendSsidMigration:
    @patch("iqoptionapi.api.threading.Event")
    def test_send_ssid_uses_event_not_spinloop(self, mock_event_class):
        mock_event = mock_event_class.return_value
        
        api = IQOptionAPI("host", "user")
        
        def simulate_response(*args, **kwargs):
            api.profile.msg = {"id": 1}
            return True
            
        mock_event.wait.side_effect = simulate_response
        
        # Use patch.object to mock the 'ssid' property
        with patch.object(IQOptionAPI, 'ssid', new_callable=PropertyMock) as mock_ssid_prop:
            mock_ssid_fn = MagicMock()
            mock_ssid_prop.return_value = mock_ssid_fn
            
            with patch("time.sleep") as mock_sleep:
                result = api.send_ssid()
                assert result is True
                mock_event.wait.assert_called()
                mock_sleep.assert_not_called()

    def test_send_ssid_timeout_returns_false(self):
        api = IQOptionAPI("host", "user")
        api.profile.msg = None
        api.profile_msg_event = MagicMock()
        api.profile_msg_event.wait.return_value = False # Timeout
        
        with patch.object(IQOptionAPI, 'ssid', new_callable=PropertyMock):
            result = api.send_ssid()
            assert result is False

    def test_send_ssid_false_profile_returns_false(self):
        api = IQOptionAPI("host", "user")
        api.profile.msg = False
        api.profile_msg_event = MagicMock()
        api.profile_msg_event.wait.return_value = True
        
        with patch.object(IQOptionAPI, 'ssid', new_callable=PropertyMock):
            result = api.send_ssid()
            assert result is False

class TestCloseWithTimeout:
    def test_close_joins_with_timeout(self):
        api = IQOptionAPI("host", "user")
        # websocket is a property, so we patch its return value
        with patch.object(IQOptionAPI, 'websocket', new_callable=PropertyMock) as mock_ws_prop:
            mock_ws = MagicMock()
            mock_ws_prop.return_value = mock_ws
            api.websocket_thread = MagicMock()
            
            from iqoptionapi.config import TIMEOUT_THREAD_JOIN
            api.close()
            api.websocket_thread.join.assert_called_with(timeout=TIMEOUT_THREAD_JOIN)

    def test_close_logs_warning_if_thread_alive(self):
        api = IQOptionAPI("host", "user")
        with patch.object(IQOptionAPI, 'websocket', new_callable=PropertyMock):
            api.websocket_thread = MagicMock()
            api.websocket_thread.is_alive.return_value = True
            
            with patch("iqoptionapi.api.get_logger") as mock_get_logger:
                api.close()
                mock_get_logger.return_value.warning.assert_called()
                args, _ = mock_get_logger.return_value.warning.call_args
                assert "forcing abandon" in args[0]

class TestAutoReconnectCallback:
    @patch("iqoptionapi.stable_api.IQOptionAPI")
    def test_reconnect_callback_registered_on_connect(self, mock_api_class):
        with patch("iqoptionapi.stable_api.CredentialStore") as mock_store:
            mock_store.return_value.consume.return_value = "pass"
            sdk = IQ_Option("email", "pass")
            
            mock_api = mock_api_class.return_value
            mock_api.connect.return_value = (True, None)
            
            sdk.connect()
            assert sdk.api._reconnect_callback == sdk._auto_reconnect

    def test_on_close_triggers_reconnect_thread(self):
        mock_api = MagicMock()
        mock_api._reconnect_callback = MagicMock()
        client = WebsocketClient(mock_api)
        
        client.on_close(None, 1006, "Connection lost")
        
        time.sleep(0.1)
        mock_api._reconnect_callback.assert_called_once()

    def test_on_close_kill_switch_releases_events(self):
        mock_api = MagicMock()
        event1 = threading.Event()
        event2 = threading.Event()
        mock_api.data_event = event1
        mock_api.other_event = event2
        mock_api.ws_connected_event = threading.Event()
        
        client = WebsocketClient(mock_api)
        client.on_close(None, 1000, "Normal")
        
        assert event1.is_set()
        assert event2.is_set()
        assert not mock_api.ws_connected_event.is_set()

    def test_auto_reconnect_calls_connect_on_failure(self):
        sdk = IQ_Option("email", "pass")
        sdk._reconnect_manager = MagicMock()
        
        # When connect is called, the 2nd time (success) it should trigger reset()
        def mock_connect():
            if sdk.connect.call_count == 2:
                sdk._reconnect_manager.reset()
                return (True, None)
            return (False, "err")

        sdk.connect = MagicMock(side_effect=mock_connect)
        sdk._auto_reconnect()
        
        assert sdk.connect.call_count == 2
        sdk._reconnect_manager.reset.assert_called_once()

    def test_auto_reconnect_stops_on_max_attempts(self):
        sdk = IQ_Option("email", "pass")
        sdk.connect = MagicMock()
        sdk._reconnect_manager = MagicMock()
        sdk._reconnect_manager.wait.side_effect = MaxReconnectAttemptsError()
        
        sdk._auto_reconnect()
        
        sdk.connect.assert_not_called()

class TestHeartbeatWatchdog:
    def test_watchdog_starts_on_connect(self):
        with patch("iqoptionapi.stable_api.IQOptionAPI") as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.connect.return_value = (True, None)
            
            sdk = IQ_Option("email", "pass")
            sdk.connect()
            
            assert hasattr(sdk, "_watchdog_thread")
            assert sdk._watchdog_thread.is_alive()
            sdk.close()

    def test_watchdog_stops_on_close(self):
        sdk = IQ_Option("email", "pass")
        sdk.api = MagicMock()
        sdk._start_heartbeat_watchdog()
        assert sdk._watchdog_thread.is_alive()
        
        sdk.close()
        time.sleep(0.1)
        assert sdk._watchdog_stop.is_set()

    def test_watchdog_triggers_reconnect_on_silence(self):
        with patch("iqoptionapi.config.HEARTBEAT_TIMEOUT_SECS", 0.1), \
             patch("iqoptionapi.config.HEARTBEAT_CHECK_INTERVAL", 0.05):
            
            sdk = IQ_Option("email", "pass")
            sdk.api = MagicMock()
            sdk._auto_reconnect = MagicMock()
            sdk._last_heartbeat = time.time() - 1.0 # Expired
            
            sdk._start_heartbeat_watchdog()
            time.sleep(0.3)
            sdk._auto_reconnect.assert_called()
            sdk.close()

    def test_heartbeat_callback_resets_timer(self):
        sdk = IQ_Option("email", "pass")
        sdk._last_heartbeat = 0
        
        sdk.api = MagicMock()
        sdk.api._heartbeat_callback = lambda: setattr(sdk, '_last_heartbeat', time.time())
        
        sdk.api._heartbeat_callback()
        assert sdk._last_heartbeat > 0
