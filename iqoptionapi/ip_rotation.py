"""
ip_rotation.py — WARP/Cloudflare IP Rotation Guard
Detecta rate limits de IQ Option y rota la IP via WARP CLI.

NOTA DE ARQUITECTURA (v8.9.993):
  La plataforma web de IQ Option funciona desde cualquier IP
  (incluyendo USA/Cloudflare), ya que la cuenta se vincula al pais
  de registro (Ecuador). La restriccion NO es geografica.
  
  Las desconexiones del SDK se deben a rate-limiting del endpoint
  auth.iqoption.com cuando se hacen demasiadas reconexiones rapidas.
  WARP rota la IP para evadir ese rate limit temporal, no para
  cambiar de pais.
  
  El geo-check se mantiene como DIAGNOSTICO (log informativo)
  pero NO bloquea la conexion.
"""
import subprocess, logging, time, json, os, platform
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# ── Feature Flag ──────────────────────────────────────────────
# Solo activo si ENABLE_IP_ROTATION=true está en el entorno.
# Útil en desarrollo Windows + WARP. En producción (Linux)
# esta variable no existe → el módulo es un no-op.
_WARP_ENABLED: bool = (
    os.environ.get("ENABLE_IP_ROTATION", "false").lower() == "true"
)

# ── Cross-platform curl ───────────────────────────────────────
# Windows usa curl.exe, Linux/macOS usa curl
_CURL_CMD: str = "curl.exe" if platform.system() == "Windows" else "curl"

_last_rotation_time: float = 0.0
_MIN_ROTATION_COOLDOWN: float = 45.0

# Senales de rate limit de IQ Option
RATE_LIMIT_SIGNALS = [
    "auth timeout", "connection refused", "429",
    "too many requests", "max retries", "timed out",
    "temporary ban"
]


def is_rate_limit_error(error_msg: str) -> bool:
    """Detecta si el error es un rate limit de auth."""
    msg = str(error_msg).lower()
    return any(signal in msg for signal in RATE_LIMIT_SIGNALS)


def get_current_ip() -> Optional[str]:
    """Obtiene la IP publica actual."""
    try:
        result = subprocess.run(
            [_CURL_CMD, "-s", "--max-time", "5", "https://api.ipify.org"],
            capture_output=True, text=True, timeout=8
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def get_ip_geo() -> Optional[Dict]:
    """
    Obtiene IP publica + geolocalizacion (diagnostico).
    Retorna dict con keys: ip, country, city, org
    """
    try:
        result = subprocess.run(
            [_CURL_CMD, "-s", "--max-time", "8", "https://ipinfo.io/json"],
            capture_output=True, text=True, timeout=12
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            return {
                "ip": data.get("ip", "unknown"),
                "country": data.get("country", "??"),
                "city": data.get("city", "unknown"),
                "org": data.get("org", "unknown"),
                "region": data.get("region", "unknown"),
            }
    except Exception as e:
        logger.debug("get_ip_geo failed: %s", e)
    return None


def log_ip_diagnostic() -> Optional[Dict]:
    """
    Log de diagnostico de la IP actual.
    Solo informativo — NO bloquea conexiones.
    La cuenta IQ Option se vincula al pais de registro,
    no a la IP de conexion.
    """
    geo = get_ip_geo()
    if geo:
        logger.info(
            "IP diagnostico: %s (%s/%s) org=%s",
            geo.get("ip"), geo.get("country"),
            geo.get("city"), geo.get("org")
        )
    else:
        logger.debug("No se pudo obtener info de IP.")
    return geo


def is_warp_available() -> bool:
    """Verifica warp-cli. Si ENABLE_IP_ROTATION=false → False."""
    if not _WARP_ENABLED:
        return False
    try:
        result = subprocess.run(
            ["warp-cli", "--version"],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def rotate_ip_warp(wait_seconds: int = 5) -> bool:
    """
    Rota la IP desconectando y reconectando WARP.
    El objetivo es obtener una IP diferente para evadir
    rate limits temporales de auth.iqoption.com.
    
    No valida geolocalizacion — IQ Option no bloquea por IP
    en cuentas demo vinculadas a paises permitidos (ej. Ecuador).
    
    Retorna True si la IP cambio exitosamente.
    """
    global _last_rotation_time

    # Respetar cooldown minimo entre rotaciones
    elapsed = time.time() - _last_rotation_time
    if elapsed < _MIN_ROTATION_COOLDOWN:
        remaining = _MIN_ROTATION_COOLDOWN - elapsed
        logger.info("Rotacion omitida: cooldown activo (%.0fs restantes)", remaining)
        return False

    if not is_warp_available():
        logger.warning("warp-cli no disponible en PATH. Rotacion no posible.")
        return False

    ip_before = get_current_ip()
    logger.info("IP antes de rotacion: %s", ip_before)

    try:
        subprocess.run(["warp-cli", "disconnect"], capture_output=True, timeout=10)
        time.sleep(2)
        subprocess.run(["warp-cli", "connect"], capture_output=True, timeout=10)
        time.sleep(wait_seconds)

        ip_after = get_current_ip()
        logger.info("IP despues de rotacion: %s", ip_after)

        _last_rotation_time = time.time()

        if ip_after and ip_after != ip_before:
            logger.info("Rotacion EXITOSA: %s -> %s", ip_before, ip_after)
            return True
        else:
            logger.warning("IP no cambio tras rotacion WARP (sigue %s).", ip_after or "desconocida")
            return False

    except FileNotFoundError:
        logger.error("warp-cli no encontrado.")
        return False
    except Exception as e:
        logger.error("Error en rotate_ip_warp: %s", e)
        return False


def connect_with_rotation(connect_fn, max_attempts: int = 3, rotate_on_fail: bool = True):
    """
    Wrapper de conexión con rotación de IP vía WARP.

    ENTORNO DE DESARROLLO (Windows + WARP instalado):
      Establece ENABLE_IP_ROTATION=true en .env
      para activar la rotación automática de IP.

    PRODUCCIÓN:
      Sin esa variable, esta función es un pass-through
      equivalente a llamar connect_fn() directamente.
      No depende de warp-cli ni curl.
    """
    if not _WARP_ENABLED:
        logger.debug(
            "ip_rotation: ENABLE_IP_ROTATION no activo, "
            "usando connect directo sin rotación."
        )
        return connect_fn()

    # Diagnostico IP (solo log)
    log_ip_diagnostic()

    for attempt in range(1, max_attempts + 1):
        logger.info("Intento de conexion %d/%d", attempt, max_attempts)
        ok, msg = connect_fn()
        if ok:
            return ok, msg

        if rotate_on_fail and is_rate_limit_error(msg):
            logger.warning(
                "Rate limit detectado: '%s'. Rotando IP WARP (intento %d)...",
                msg, attempt
            )
            rotated = rotate_ip_warp(wait_seconds=8)
            if not rotated:
                # Si no se pudo rotar, esperar para que el rate limit expire naturalmente
                wait_time = 60
                logger.warning(
                    "No se pudo rotar IP. Esperando %ds para que expire rate limit...",
                    wait_time
                )
                time.sleep(wait_time)
        else:
            # Error no relacionado con rate limit — no tiene sentido rotar
            return ok, msg

    return False, "Fallidos %d intentos con rotacion de IP" % max_attempts
