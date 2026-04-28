"""
ip_rotation.py — WARP/Cloudflare IP Rotation Guard
Detecta rate limits de IQ Option y rota la IP via WARP CLI.

IMPORTANTE: IQ Option bloquea conexiones desde ciertos paises
(USA, Japon, Israel, Canada, Australia, UE parcial).
WARP asigna IPs de Cloudflare que frecuentemente caen en USA,
lo que causa desconexiones inmediatas post-auth.

Este modulo valida la geolocalizacion de la IP asignada
y reintenta la rotacion si cae en un pais restringido.
"""
import subprocess, logging, time, json
from typing import Optional, Dict

logger = logging.getLogger(__name__)

_last_rotation_time: float = 0.0
_MIN_ROTATION_COOLDOWN: float = 45.0  # segundos minimos entre rotaciones

# Senales de rate limit de IQ Option
RATE_LIMIT_SIGNALS = [
    "auth timeout", "connection refused", "429",
    "too many requests", "max retries", "timed out",
    "temporary ban"
]

# Paises donde IQ Option bloquea o restringe el acceso
# Si la IP de WARP cae en alguno de estos, la rotacion se considera fallida
BLOCKED_COUNTRIES = {
    "US",  # USA — regulacion CFTC/SEC, bloqueo total
    "JP",  # Japon — JFSA prohibe binary options
    "IL",  # Israel — ISA prohibe binary options
    "CA",  # Canada — provincial bans
    "AU",  # Australia — ASIC restricciones
    "BE",  # Belgica — ban total binary options
    "FR",  # Francia — AMF restricciones
}

# Paises ideales para IQ Option (sin restricciones conocidas)
PREFERRED_COUNTRIES = {
    "EC",  # Ecuador — tu pais real
    "BR",  # Brasil
    "CO",  # Colombia
    "PE",  # Peru
    "MX",  # Mexico
    "CL",  # Chile
    "AR",  # Argentina
    "PY",  # Paraguay
    "UY",  # Uruguay
    "PA",  # Panama
    "GB",  # UK (permitido para opciones digitales)
    "DE",  # Alemania
    "IN",  # India
    "TH",  # Tailandia
    "PH",  # Filipinas
    "NG",  # Nigeria
    "ZA",  # Sudafrica
}


def is_rate_limit_error(error_msg: str) -> bool:
    """Detecta si el error es un rate limit de auth."""
    msg = str(error_msg).lower()
    return any(signal in msg for signal in RATE_LIMIT_SIGNALS)


def get_current_ip() -> Optional[str]:
    """Obtiene la IP publica actual."""
    try:
        result = subprocess.run(
            ["curl.exe", "-s", "--max-time", "5", "https://api.ipify.org"],
            capture_output=True, text=True, timeout=8
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def get_ip_geo() -> Optional[Dict]:
    """
    Obtiene IP publica + geolocalizacion.
    Retorna dict con keys: ip, country, city, org
    """
    try:
        result = subprocess.run(
            ["curl.exe", "-s", "--max-time", "8", "https://ipinfo.io/json"],
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


def is_ip_safe_for_iq(geo: Optional[Dict] = None) -> bool:
    """
    Verifica si la IP actual es segura para conectarse a IQ Option.
    Una IP es insegura si su pais esta en BLOCKED_COUNTRIES.
    """
    if geo is None:
        geo = get_ip_geo()
    if geo is None:
        logger.warning("No se pudo verificar geolocalizacion de IP. Asumiendo segura.")
        return True  # fail-open: si no podemos verificar, intentamos igual
    
    country = geo.get("country", "??")
    if country in BLOCKED_COUNTRIES:
        logger.warning(
            "IP %s esta en pais BLOQUEADO: %s (%s). IQ Option rechazara la conexion.",
            geo.get("ip"), country, geo.get("city")
        )
        return False
    
    if country in PREFERRED_COUNTRIES:
        logger.info("IP %s en pais PREFERIDO: %s (%s)", geo.get("ip"), country, geo.get("city"))
    else:
        logger.info("IP %s en pais %s (%s) — no bloqueado", geo.get("ip"), country, geo.get("city"))
    return True


def is_warp_available() -> bool:
    """Verifica si warp-cli esta instalado y accesible en el PATH."""
    try:
        result = subprocess.run(
            ["warp-cli", "--version"],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def rotate_ip_warp(wait_seconds: int = 5, max_geo_retries: int = 3) -> bool:
    """
    Rota la IP desconectando y reconectando WARP.
    Valida que la nueva IP NO caiga en un pais restringido.
    Si cae en pais bloqueado, reintenta hasta max_geo_retries veces.
    
    Retorna True solo si la IP cambio Y es segura para IQ Option.
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

    geo_before = get_ip_geo()
    ip_before = geo_before.get("ip") if geo_before else get_current_ip()
    logger.info("IP antes de rotacion: %s (%s/%s)",
                ip_before,
                geo_before.get("country", "?") if geo_before else "?",
                geo_before.get("city", "?") if geo_before else "?")

    for geo_attempt in range(1, max_geo_retries + 1):
        try:
            subprocess.run(["warp-cli", "disconnect"], capture_output=True, timeout=10)
            time.sleep(2)
            subprocess.run(["warp-cli", "connect"], capture_output=True, timeout=10)
            time.sleep(wait_seconds)

            geo_after = get_ip_geo()
            ip_after = geo_after.get("ip") if geo_after else get_current_ip()

            if not ip_after:
                logger.warning("No se pudo obtener IP post-rotacion (intento geo %d)", geo_attempt)
                continue

            country = geo_after.get("country", "??") if geo_after else "??"
            city = geo_after.get("city", "?") if geo_after else "?"

            logger.info("IP post-rotacion (intento %d): %s (%s/%s)",
                        geo_attempt, ip_after, country, city)

            # Validar que no caimos en pais bloqueado
            if geo_after and not is_ip_safe_for_iq(geo_after):
                logger.warning(
                    "IP %s cayo en pais bloqueado %s. Reintentando rotacion (%d/%d)...",
                    ip_after, country, geo_attempt, max_geo_retries
                )
                time.sleep(2)  # breve pausa antes de reintentar
                continue

            # IP cambio y es segura
            if ip_after != ip_before:
                logger.info("Rotacion EXITOSA: %s -> %s (%s/%s)",
                            ip_before, ip_after, country, city)
                _last_rotation_time = time.time()
                return True
            else:
                logger.warning("IP no cambio tras rotacion WARP (sigue %s).", ip_after)
                _last_rotation_time = time.time()
                return False

        except FileNotFoundError:
            logger.error("warp-cli no encontrado.")
            return False
        except Exception as e:
            logger.error("Error en rotate_ip_warp: %s", e)
            return False

    # Agotamos intentos sin conseguir IP segura
    logger.error(
        "Agotados %d intentos de rotacion geo. "
        "Todas las IPs cayeron en paises bloqueados. "
        "Considere usar VPN manual con servidor en Latinoamerica.",
        max_geo_retries
    )
    _last_rotation_time = time.time()
    return False


def connect_with_rotation(connect_fn, max_attempts: int = 3, rotate_on_fail: bool = True):
    """
    Wrapper para connect() que rota la IP ante rate limits.
    Valida geolocalizacion ANTES de intentar conectar.

    Uso:
      ok, msg = connect_with_rotation(api.connect)
    """
    for attempt in range(1, max_attempts + 1):
        # Verificar geo antes de conectar (solo en primer intento o post-rotacion)
        if attempt == 1:
            geo = get_ip_geo()
            if geo and not is_ip_safe_for_iq(geo):
                logger.warning(
                    "IP actual (%s/%s) en pais bloqueado. Rotando antes de conectar...",
                    geo.get("ip"), geo.get("country")
                )
                if rotate_on_fail:
                    rotated = rotate_ip_warp(wait_seconds=8, max_geo_retries=3)
                    if not rotated:
                        logger.warning("No se pudo obtener IP segura. Intentando conectar de todas formas.")

        logger.info("Intento de conexion %d/%d", attempt, max_attempts)
        ok, msg = connect_fn()
        if ok:
            return ok, msg

        if rotate_on_fail and is_rate_limit_error(msg):
            logger.warning(
                "Rate limit detectado: '%s'. Rotando IP WARP (intento %d)...",
                msg, attempt
            )
            rotated = rotate_ip_warp(wait_seconds=8, max_geo_retries=3)
            if not rotated:
                logger.error("No se pudo rotar IP. Esperando 60s...")
                time.sleep(60)
        else:
            # Error no relacionado con rate limit
            return ok, msg

    return False, "Fallidos %d intentos con rotacion de IP" % max_attempts
