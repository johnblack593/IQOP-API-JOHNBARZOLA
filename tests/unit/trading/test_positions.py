import pytest
import threading

class TestCheckWin:
    def test_check_win_timeout_returns_none(self, mock_iq):
        # El event store estará vacío, por lo que disparará el timeout
        result = mock_iq.check_win("test_123", timeout=0.01)
        assert result is None

    def test_check_win_v2_timeout_returns_none(self, mock_iq):
        result = mock_iq.check_win_v2("test_123", timeout=0.01)
        assert result is None

    def test_check_win_digital_timeout_returns_none(self, mock_iq):
        result = mock_iq.check_win_digital("test_123", timeout=0.01)
        assert result is None

    def test_check_win_with_populated_event_returns_result(self, mock_iq):
        order_id = 999
        # Simular que el evento ya llegó (Binary path)
        # Asegurar que el store es un dict real y no un MagicMock
        mock_iq.api.game_betinfo = {}
        mock_iq.api.game_betinfo[order_id] = {"win": "win"}
        mock_iq.api.result_event_store[order_id].set()
        
        result = mock_iq.check_win(order_id, timeout=1)
        assert result == "win"

class TestClosePosition:
    def test_close_position_calls_api(self, mock_iq):
        mock_iq.api.close_position_data = {"status": 2000}
        mock_iq.api.close_position.side_effect = lambda pid: mock_iq.api.close_position_event.set()
        res = mock_iq.close_position("pos_1")
        assert res is True

    def test_close_position_v2_with_timeout(self, mock_iq):
        mock_iq.api.close_position.side_effect = lambda pid: mock_iq.api.close_position_event.set()
        res = mock_iq.close_position_v2("pos_1")
        assert res is True
