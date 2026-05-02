"""
iqoptionapi/core/asset_taxonomy.py
────────────────────────────────────
Taxonomía de activos IQ Option 2026.
Define dos grupos operativos con reglas de ejecución distintas:
  - OPCIONES: Binary, Digital, Blitz/Turbo
  - MARGEN/CFD: Forex, Acciones, Cripto, Índices, Materias, Fondos
"""
from __future__ import annotations
from enum import Enum
from typing import NamedTuple
from iqoptionapi.strategy.signal import AssetType


class OperationGroup(str, Enum):
    """Grupo operativo del activo."""
    OPTIONS = "options"    # vencimiento fijo, todo-o-nada
    MARGIN  = "margin"     # CFD con apalancamiento, TP/SL


class AssetRules(NamedTuple):
    """Reglas de ejecución para un AssetType."""
    group:           OperationGroup
    needs_duration:  bool    # True  → buy_v2() requiere duration en segundos
    needs_leverage:  bool    # True  → buy_order() requiere leverage
    needs_tp_sl:     bool    # True  → TP/SL obligatorios para risk management
    max_leverage:    int     # 0 si no aplica
    is_otc_capable:  bool    # True si tiene variante OTC (sufijo -OTC en nombre)
    instrument_type: str     # string que el WS espera (e.g. "forex", "crypto")
    group_ids:       tuple   # group_ids del servidor asociados


# Mapa canónico de reglas por AssetType
ASSET_RULES: dict[AssetType, AssetRules] = {
    AssetType.BINARY: AssetRules(
        group=OperationGroup.OPTIONS,
        needs_duration=True,
        needs_leverage=False,
        needs_tp_sl=False,
        max_leverage=0,
        is_otc_capable=True,
        instrument_type="binary-option",
        group_ids=(),
    ),
    AssetType.DIGITAL: AssetRules(
        group=OperationGroup.OPTIONS,
        needs_duration=True,
        needs_leverage=False,
        needs_tp_sl=False,
        max_leverage=0,
        is_otc_capable=True,
        instrument_type="digital-option",
        group_ids=(),
    ),
    AssetType.TURBO: AssetRules(
        group=OperationGroup.OPTIONS,
        needs_duration=True,
        needs_leverage=False,
        needs_tp_sl=False,
        max_leverage=0,
        is_otc_capable=True,
        instrument_type="turbo-option",
        group_ids=(),
    ),
    AssetType.FOREX: AssetRules(
        group=OperationGroup.MARGIN,
        needs_duration=False,
        needs_leverage=True,
        needs_tp_sl=True,
        max_leverage=1000,
        is_otc_capable=False,
        instrument_type="forex",
        group_ids=(1,),
    ),
    AssetType.CRYPTO: AssetRules(
        group=OperationGroup.MARGIN,
        needs_duration=False,
        needs_leverage=True,
        needs_tp_sl=True,
        max_leverage=200,
        is_otc_capable=False,
        instrument_type="crypto",
        group_ids=(16,),
    ),
    AssetType.STOCKS: AssetRules(
        group=OperationGroup.MARGIN,
        needs_duration=False,
        needs_leverage=True,
        needs_tp_sl=True,
        max_leverage=100,
        is_otc_capable=False,
        instrument_type="stocks",
        group_ids=(2,),
    ),
    AssetType.COMMODITIES: AssetRules(
        group=OperationGroup.MARGIN,
        needs_duration=False,
        needs_leverage=True,
        needs_tp_sl=True,
        max_leverage=150,
        is_otc_capable=False,
        instrument_type="commodities",
        group_ids=(3,),
    ),
    AssetType.INDICES: AssetRules(
        group=OperationGroup.MARGIN,
        needs_duration=False,
        needs_leverage=True,
        needs_tp_sl=True,
        max_leverage=200,
        is_otc_capable=False,
        instrument_type="indices",
        group_ids=(4,),
    ),
    AssetType.ETF: AssetRules(
        group=OperationGroup.MARGIN,
        needs_duration=False,
        needs_leverage=True,
        needs_tp_sl=True,
        max_leverage=100,
        is_otc_capable=False,
        instrument_type="etf",
        group_ids=(41,),
    ),
}

MARGIN_ASSET_TYPES: frozenset[AssetType] = frozenset({
    AssetType.FOREX, AssetType.CRYPTO, AssetType.STOCKS,
    AssetType.COMMODITIES, AssetType.INDICES, AssetType.ETF,
})

OPTIONS_ASSET_TYPES: frozenset[AssetType] = frozenset({
    AssetType.BINARY, AssetType.DIGITAL, AssetType.TURBO,
})


class TaxonomyError(ValueError):
    """Se lanza cuando un Signal es incompatible con el AssetType/grupo."""


def get_rules(asset_type: AssetType) -> AssetRules:
    """Retorna las reglas de ejecución para el AssetType dado."""
    try:
        return ASSET_RULES[asset_type]
    except KeyError:
        raise TaxonomyError(f"AssetType desconocido: {asset_type!r}")


def get_asset_type_from_group_id(group_id: int) -> AssetType | None:
    """
    Retorna el AssetType que corresponde a un group_id del servidor.
    Retorna None si el group_id no tiene mapeo conocido.
    """
    for asset_type, rules in ASSET_RULES.items():
        if group_id in rules.group_ids:
            return asset_type
    return None


def is_margin_asset(asset_type: AssetType) -> bool:
    """True si el activo pertenece al grupo de Margen/CFD."""
    return asset_type in MARGIN_ASSET_TYPES


def is_options_asset(asset_type: AssetType) -> bool:
    """True si el activo pertenece al grupo de Opciones."""
    return asset_type in OPTIONS_ASSET_TYPES


def validate_signal(signal) -> None:
    """
    Valida que los campos de un Signal sean compatibles con su AssetType.
    Lanza TaxonomyError con mensaje descriptivo si hay inconsistencia.

    Reglas:
    - OPCIONES: duration > 0 obligatorio
    - MARGEN: duration debe ser 0 (no aplica)
    """
    rules = get_rules(signal.asset_type)

    if rules.needs_duration and signal.duration <= 0:
        raise TaxonomyError(
            f"Signal para {signal.asset_type.value} requiere duration > 0, "
            f"recibido: {signal.duration}"
        )
    if not rules.needs_duration and signal.duration > 0:
        raise TaxonomyError(
            f"Signal para {signal.asset_type.value} (Margen) no debe "
            f"tener duration. Usa duration=0. Recibido: {signal.duration}"
        )


def is_otc_asset(asset_name: str) -> bool:
    """
    True si el nombre del activo es una variante OTC.
    Ejemplos: 'EURUSD-OTC', 'ONDO-OTC' → True
              'EURUSD', 'BTCUSD'        → False
    """
    return str(asset_name).upper().endswith("-OTC")


def normalize_asset_name(asset_name: str, asset_type: AssetType) -> str:
    """
    Normaliza el nombre del activo para la API IQ Option.
    - OPCIONES OTC: si el nombre no termina en '-OTC' y es fin de semana
      o mercado cerrado, el bot debería usar la variante OTC.
    - MARGEN: retorna el nombre en mayúsculas limpio.
    """
    name = asset_name.strip().upper()
    rules = get_rules(asset_type)
    if not rules.is_otc_capable and name.endswith("-OTC"):
        raise TaxonomyError(
            f"AssetType {asset_type.value} no soporta variantes OTC: {name}"
        )
    return name
