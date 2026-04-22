"""
iqoptionapi/validator.py
─────────────────────────
Validaciones de parámetros de trading para JCBV-NEXUS.

Todas las funciones lanzan ValueError con mensajes descriptivos.
Nunca retornan None silenciosamente. Usar antes de enviar órdenes
para proteger contra pérdidas por parámetros inválidos.
"""
from iqoptionapi.config import VALID_CANDLE_SIZES


class TradingValidationError(ValueError):
    """
    Error específico de validación de parámetros de trading.
    Subclase de ValueError para compatibilidad con código existente.
    Incluye el parámetro que causó el error en self.param.
    """
    def __init__(self, message: str, param: str = "") -> None:
        super().__init__(message)
        self.param = param


def validate_amount(amount: float, min_amount: float = 1.0) -> None:
    """
    Valida que el monto de la operación sea válido.
    - Debe ser un número (int o float)
    - Debe ser mayor que min_amount (default: 1.0 USD)
    - No puede ser NaN ni infinito
    Lanza TradingValidationError si falla.
    """
    import math
    if not isinstance(amount, (int, float)):
        raise TradingValidationError(
            f"amount debe ser numérico, recibido: {type(amount).__name__}",
            param="amount"
        )
    if math.isnan(amount) or math.isinf(amount):
        raise TradingValidationError(
            f"amount no puede ser NaN ni infinito: {amount}",
            param="amount"
        )
    if amount < min_amount:
        raise TradingValidationError(
            f"amount={amount} es menor al mínimo permitido ({min_amount})",
            param="amount"
        )


def validate_action(action: str) -> str:
    """
    Valida y normaliza la dirección de la operación.
    Acepta: 'call', 'put', 'buy', 'sell', 'C', 'P' (case-insensitive)
    Retorna el valor normalizado en minúsculas: 'call' o 'put'
    Lanza TradingValidationError si el valor no es reconocido.
    """
    normalized = action.strip().lower()
    CALL_ALIASES = {"call", "buy", "c"}
    PUT_ALIASES  = {"put", "sell", "p"}
    if normalized in CALL_ALIASES:
        return "call"
    if normalized in PUT_ALIASES:
        return "put"
    raise TradingValidationError(
        f"action='{action}' no válido. Use 'call'/'put'/'buy'/'sell'/'C'/'P'",
        param="action"
    )


def validate_candle_size(size: int) -> None:
    """
    Valida que el tamaño de vela sea soportado por IQ Option.
    Los tamaños válidos están definidos en config.VALID_CANDLE_SIZES.
    Lanza TradingValidationError si el tamaño no es válido.
    """
    if size not in VALID_CANDLE_SIZES:
        raise TradingValidationError(
            f"candle size={size}s no soportado. "
            f"Válidos: {sorted(VALID_CANDLE_SIZES)}",
            param="size"
        )


def validate_duration(duration: int, option_type: str = "binary") -> None:
    """
    Valida la duración de expiración según el tipo de opción.
    - binary/turbo: 1, 2, 3, 4, 5 minutos
    - digital: 1, 2, 3, 4, 5 minutos
    - blitz: 5, 10, 15, 20, 30, 45 segundos (tipo especial)
    Lanza TradingValidationError si la duración no es válida para el tipo.
    """
    BINARY_DURATIONS  = {1, 2, 3, 4, 5}
    DIGITAL_DURATIONS = {1, 2, 3, 4, 5}
    BLITZ_DURATIONS   = {5, 10, 15, 20, 30, 45}

    ot = option_type.lower()
    if ot in ("binary", "turbo"):
        valid = BINARY_DURATIONS
    elif ot == "digital":
        valid = DIGITAL_DURATIONS
    elif ot == "blitz":
        valid = BLITZ_DURATIONS
    else:
        raise TradingValidationError(
            f"option_type='{option_type}' no reconocido. "
            f"Use 'binary'/'turbo'/'digital'/'blitz'",
            param="option_type"
        )

    if duration not in valid:
        raise TradingValidationError(
            f"duration={duration} no válido para {option_type}. "
            f"Válidos: {sorted(valid)}",
            param="duration"
        )


def validate_active(active: str, actives_map: dict) -> None:
    """
    Valida que el activo exista en el mapa de ACTIVES del SDK.
    actives_map: OP_code.ACTIVES (o cualquier dict {name: id})
    Lanza TradingValidationError si el activo no está en el mapa.
    Útil antes de buy() para evitar KeyError en producción.
    """
    if active not in actives_map:
        # Intentar sugerir activos similares (case-insensitive fuzzy)
        close = [k for k in actives_map if active.upper() in k.upper()]
        suggestion = f" ¿Quisiste decir: {close[:3]}?" if close else ""
        raise TradingValidationError(
            f"Activo '{active}' no encontrado en ACTIVES.{suggestion}",
            param="active"
        )


def validate_sl_tp(
    stop_lose_kind: str | None,
    stop_lose_value: float | None,
    take_profit_kind: str | None,
    take_profit_value: float | None,
) -> None:
    """
    Valida los parámetros de Stop Loss y Take Profit.
    - Si kind no es None, value debe existir y ser > 0
    - kind acepta: 'percent', 'price', 'pnl'
    - Si ambos son None, se permite (sin SL/TP)
    Lanza TradingValidationError si la combinación no es válida.
    """
    VALID_KINDS = {"percent", "price", "pnl"}

    for prefix, kind, value in [
        ("stop_lose", stop_lose_kind, stop_lose_value),
        ("take_profit", take_profit_kind, take_profit_value),
    ]:
        if kind is None:
            continue
        if kind not in VALID_KINDS:
            raise TradingValidationError(
                f"{prefix}_kind='{kind}' no válido. Use: {VALID_KINDS}",
                param=f"{prefix}_kind"
            )
        if value is None or value <= 0:
            raise TradingValidationError(
                f"{prefix}_value debe ser > 0 cuando {prefix}_kind='{kind}'",
                param=f"{prefix}_value"
            )
