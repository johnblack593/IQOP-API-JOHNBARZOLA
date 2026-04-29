def test_stable_api_has_no_business_logic():
    """
    stable_api.py debe ser < 900 líneas (fachada, no implementación).
    """
    import pathlib
    lines = len(pathlib.Path(
        "iqoptionapi/stable_api.py"
    ).read_text().splitlines())
    assert lines < 900, (
        f"stable_api.py tiene {lines} líneas. "
        f"Supera el límite de 900 — agregar lógica de negocio "
        f"directo viola el patrón Fachada."
    )

def test_all_mixins_importable():
    """Todos los Mixins deben importar sin errores."""
    from iqoptionapi.mixins.orders_mixin import OrdersMixin
    from iqoptionapi.mixins.positions_mixin import PositionsMixin
    from iqoptionapi.mixins.streams_mixin import StreamsMixin
    from iqoptionapi.mixins.management_mixin import ManagementMixin
    assert all([OrdersMixin, PositionsMixin,
                StreamsMixin, ManagementMixin])

def test_iq_option_inherits_all_mixins():
    from iqoptionapi.stable_api import IQ_Option
    from iqoptionapi.mixins.orders_mixin import OrdersMixin
    from iqoptionapi.mixins.positions_mixin import PositionsMixin
    assert issubclass(IQ_Option, OrdersMixin)
    assert issubclass(IQ_Option, PositionsMixin)
