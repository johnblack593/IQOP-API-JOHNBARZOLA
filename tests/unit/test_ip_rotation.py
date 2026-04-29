import os, pytest
from unittest.mock import patch, MagicMock

def test_warp_disabled_by_default():
    """Sin ENABLE_IP_ROTATION, el módulo es no-op."""
    with patch.dict(os.environ, {}, clear=True):
        import importlib
        import iqoptionapi.ip_rotation as mod
        importlib.reload(mod)
        assert mod._WARP_ENABLED is False

def test_connect_with_rotation_passthrough_when_disabled():
    """Con flag desactivado, connect_with_rotation llama a
    connect_fn directamente sin intentar warp."""
    with patch.dict(os.environ, {"ENABLE_IP_ROTATION": "false"}):
        import importlib
        import iqoptionapi.ip_rotation as mod
        importlib.reload(mod)
        mock_connect = MagicMock(return_value=(True, "ok"))
        result = mod.connect_with_rotation(mock_connect)
        mock_connect.assert_called_once()
        assert result == (True, "ok")

def test_is_warp_available_false_when_disabled():
    """is_warp_available retorna False si flag está desactivado."""
    with patch.dict(os.environ, {"ENABLE_IP_ROTATION": "false"}):
        import importlib
        import iqoptionapi.ip_rotation as mod
        importlib.reload(mod)
        assert mod.is_warp_available() is False

def test_curl_cmd_crossplatform():
    """_CURL_CMD es 'curl' en Linux, 'curl.exe' en Windows."""
    import iqoptionapi.ip_rotation as mod
    import platform
    expected = "curl.exe" if platform.system() == "Windows" else "curl"
    assert mod._CURL_CMD == expected
