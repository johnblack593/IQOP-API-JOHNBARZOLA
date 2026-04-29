"""
Regresión: Garantiza que ningún método del SDK bloquea
indefinidamente (Sprint 0 fix — bucles infinitos eliminados).
"""
import ast, pathlib, pytest

STABLE_API_SRC = pathlib.Path(
    "iqoptionapi/stable_api.py"
).read_text(encoding="utf-8")

def _get_while_true_lines(source: str) -> list[int]:
    """Retorna líneas donde aparece 'while True' en lógica de espera."""
    tree = ast.parse(source)
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            # Detectar while True (Constant True o nombre True)
            cond = node.test
            if (isinstance(cond, ast.Constant) and cond.value is True):
                lines.append(node.lineno)
    return lines

def test_no_while_true_in_stable_api():
    """stable_api.py no debe tener 'while True' en lógica de espera."""
    offending = _get_while_true_lines(STABLE_API_SRC)
    assert offending == [], (
        f"Se encontraron while True en stable_api.py líneas: "
        f"{offending}. Esto puede causar bloqueo de threads."
    )

def test_no_rate_limiter_references():
    """No deben quedar referencias al atributo eliminado _rate_limiter."""
    assert "_rate_limiter" not in STABLE_API_SRC, (
        "Referencia a _rate_limiter encontrada en stable_api.py. "
        "Debe usarse _order_bucket con @rate_limited."
    )

def test_check_win_returns_none_on_timeout(mock_iq):
    """check_win retorna None en lugar de bloquear cuando no hay evento."""
    result = mock_iq.check_win("test_order_123", timeout=0.1)
    assert result is None, (
        "check_win debe retornar None en timeout, no bloquear."
    )

def test_check_win_digital_returns_none_on_timeout(mock_iq):
    """check_win_digital retorna None en timeout sin bloquear."""
    result = mock_iq.check_win_digital("test_order_123", timeout=0.1)
    assert result is None
