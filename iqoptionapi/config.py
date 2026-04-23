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
import os

# --- Timeouts (segundos) ---
TIMEOUT_WS_CONNECT: int = 15
TIMEOUT_WS_DATA: int = 30
TIMEOUT_CANDLE_STREAM: int = 20
TIMEOUT_LEADER_BOARD: int = 15
TIMEOUT_BALANCE_RESET: int = 15
TIMEOUT_SSID_AUTH: int = 15
TIMEOUT_ALL_INIT: int = 30      # para get_all_init
TIMEOUT_THREAD_JOIN: float = 5.0  # para api.py close() BUG-WS-01

# --- Heartbeat watchdog ---
HEARTBEAT_TIMEOUT_SECS: float = 30.0   # segundos sin heartbeat antes de forzar reconexión
HEARTBEAT_CHECK_INTERVAL: float = 10.0  # cada cuántos segundos el watchdog revisa

# --- Polling intervals (segundos) ---
# ADVERTENCIA: estos valores existen solo para compatibilidad
# con código legacy. Todo código nuevo usa threading.Event.wait().
POLLING_INTERVAL_FAST: float = 0.05   # 50ms — eventos de datos WS
POLLING_INTERVAL_SLOW: float = 0.5    # 500ms — operaciones lentas

# MIGRACIÓN: estos valores se eliminan cuando todos los spin-loops
# sean migrados a threading.Event.wait(). Ver S1-02 tracking.
_SPINLOOP_METHODS_REMAINING: int = 0   # Deuda técnica eliminada exitosamente

# --- Rate limiting ---
RATE_LIMIT_CAPACITY: float = 5.0    # tokens máximos en bucket
RATE_LIMIT_REFILL: float = 0.5      # tokens por segundo

# BURST: número máximo de órdenes que el bot puede enviar en ráfaga
# antes de que el token bucket se agote. Igual a RATE_LIMIT_CAPACITY.
RATE_LIMIT_BURST: int = 5

# COOLDOWN mínimo entre órdenes del mismo activo (segundos).
# No lo aplica el SDK directamente, pero el bot de JCBV-NEXUS
# debe respetarlo para evitar duplicados en opciones binarias.
ORDER_COOLDOWN_SECS: float = 2.0

# --- Reconexión ---
RECONNECT_BASE_DELAY: float = 2.0   # base exponencial (segundos)
RECONNECT_MAX_DELAY: float = 60.0   # techo máximo (segundos)
MAX_RECONNECT_ATTEMPTS: int = 10    # intentos antes de error
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

# --- Signal Engine ---
SIGNAL_MIN_CONFIDENCE: float = 0.5    # umbral mínimo para ejecutar señal
SIGNAL_MAX_AMOUNT:     float = 10.0   # monto máximo por operación (USD)
SIGNAL_DEFAULT_DURATION: int = 60     # duración por defecto (segundos)
CANDLE_HISTORY_SIZE:   int = 100      # velas a cargar para análisis

# --- Circuit Breaker ---
CB_MAX_CONSECUTIVE_LOSSES: int   = 3
CB_MAX_SESSION_LOSS_USD:   float = 10.0
CB_MAX_DRAWDOWN_PCT:       float = 0.10
CB_RECOVERY_WAIT_SECS:     float = 300.0

# --- Trade Journal ---
JOURNAL_DIR: str = "data/journal"

# --- Asset Scanner ---
SCANNER_MIN_PAYOUT:       float = 0.80   # 80% mínimo
SCANNER_OPTIMAL_VOL:      float = 0.40   # volatilidad óptima normalizada
SCANNER_MIN_SCORE:        float = 0.60   # score mínimo para operar

# --- Money Management ---
MM_DEFAULT_STRATEGY:   str   = "flat"
MM_BASE_AMOUNT:        float = 1.0
MM_MAX_STEPS:          int   = 4
MM_MAX_AMOUNT_USD:     float = 50.0
MM_MAX_BALANCE_PCT:    float = 0.05

# --- Signal Consensus ---
CONSENSUS_MIN_AGREEMENT: float = 0.66
CONSENSUS_MIN_SCORE:     float = 0.60

# --- Candle Cache ---
CACHE_DIR:           str = "data/candles"
CANDLE_BUFFER_MAX:   int = int(os.getenv("CANDLE_BUFFER_MAX", "500"))
CANDLE_TTL_SECONDS:  int = int(os.getenv("CANDLE_TTL_SECONDS", "86400"))  # 24h
CACHE_MAX_DISK_DAYS: int = 30
