"""
Verifica que HTTP y WebSocket usan el mismo perfil de Chrome 124.
"""
def test_http_user_agent_is_chrome():
    from iqoptionapi.http.session import CHROME_HEADERS, USER_AGENT
    ua = USER_AGENT
    assert "Chrome/124" in ua, f"User-Agent incorrecto: {ua}"
    assert "Mozilla/5.0" in ua

def test_accept_language_is_latam():
    from iqoptionapi.http.session import CHROME_HEADERS
    lang = CHROME_HEADERS.get("Accept-Language", "")
    assert "es-419" in lang, (
        f"Accept-Language debe incluir es-419, actual: {lang}"
    )

def test_http_and_ws_user_agent_identical():
    """HTTP y WS deben usar exactamente el mismo User-Agent string."""
    from iqoptionapi.http.session import USER_AGENT as HTTP_UA
    from iqoptionapi.api import WS_USER_AGENT
    assert HTTP_UA == WS_USER_AGENT, (
        f"Fingerprint inconsistente:\n"
        f"  HTTP: {HTTP_UA}\n"
        f"  WS:   {WS_USER_AGENT}"
    )

def test_ws_origin_header():
    from iqoptionapi.api import WS_ORIGIN
    assert WS_ORIGIN == "https://iqoption.com", (
        f"WS Origin incorrecto: {WS_ORIGIN}"
    )
