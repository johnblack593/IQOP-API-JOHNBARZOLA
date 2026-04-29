"""
iqoptionapi/utils.py
─────────────────────
Utilidades compartidas del SDK. Importar desde aquí para evitar
duplicación entre módulos.
"""
from collections import defaultdict
from typing import Any, Callable


def nested_dict(n: int, type_factory: Callable[[], Any]) -> defaultdict:
    """
    Crea un defaultdict anidado de profundidad n.

    Args:
        n: profundidad del anidamiento (1 = un nivel, 2 = dos niveles...)
        type_factory: callable que produce el valor por defecto en la hoja

    Example:
        d = nested_dict(2, dict)   # defaultdict de defaultdict de dict
        d["EUR"]["USD"]["price"] = 1.08
    """
    if n == 1:
        return defaultdict(type_factory)
    return defaultdict(lambda: nested_dict(n - 1, type_factory))
