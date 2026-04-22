"""
iqoptionapi/config.py
─────────────────────
Fuente única de verdad para todas las constantes operacionales del SDK.

Para sobreescribir valores en tiempo de ejecución, usa variables de
entorno (ver ENV_* al final de este módulo) o instancia los componentes
con parámetros explícitos:
    TokenBucket(capacity=10.0, refill_rate=1.0)
    ReconnectManager(max_attempts=5)

NUNCA importar constantes de este módulo en tests unitarios que
requieran valores distintos — pasa los valores como parámetros.
"""

# --- Timeouts (segundos) ---
TIMEOUT_WS_CONNECT: int = 15
TIMEOUT_WS_DATA: int = 30
TIMEOUT_CANDLE_STREAM: int = 20
TIMEOUT_LEADERBOARD: int = 15
TIMEOUT_BALANCE_RESET: int = 15
TIMEOUT_SSID_AUTH: int = 15
TIMEOUT_ALL_INIT: int = 30      # para get_all_init
TIMEOUT_THREAD_JOIN: float = 5.0  # para api.py close() BUG-WS-01

# --- Polling intervals (segundos) ---
# ADVERTENCIA: estos valores existen solo para compatibilidad
# con código legacy. Todo código nuevo usa threading.Event.wait().
POLLING_FAST: float = 0.05   # 50ms — eventos de datos WS
POLLING_SLOW: float = 0.5    # 500ms — operaciones lentas

# --- Rate limiting ---
RATE_LIMIT_CAPACITY: float = 5.0    # tokens máximos en bucket
RATE_LIMIT_REFILL: float = 0.5      # tokens por segundo

# --- Reconexión ---
RECONNECT_BASE_DELAY: float = 2.0   # base exponencial (segundos)
RECONNECT_MAX_DELAY: float = 60.0   # techo máximo (segundos)
RECONNECT_MAX_ATTEMPTS: int = 10    # intentos antes de error
RECONNECT_JITTER: float = 0.5       # ±50% jitter

# --- Candle sizes válidos (segundos) ---
VALID_CANDLE_SIZES: tuple[int, ...] = (
    1, 5, 10, 15, 30, 60, 120, 300, 600, 900,
    1800, 3600, 7200, 14400, 28800, 43200,
    86400, 604800, 2592000
)

# --- Nombres de variables de entorno ---
ENV_EMAIL: str = "IQ_EMAIL"
ENV_PASSWORD: str = "IQ_PASSWORD"
ENV_ACCOUNT_TYPE: str = "IQ_ACCOUNT_TYPE"
