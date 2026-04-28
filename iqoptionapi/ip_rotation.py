"""
ip_rotation.py — WARP/Cloudflare IP Rotation Guard
Detecta rate limits de IQ Option y rota la IP via WARP CLI.
"""
import subprocess, socket, logging, time
from typing import Optional

logger = logging.getLogger(__name__)

_last_rotation_time: float = 0.0
_MIN_ROTATION_COOLDOWN: float = 45.0  # segundos mínimos entre rotaciones

# Señales de rate limit de IQ Option
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
    """Obtiene la IP pública actual via DNS."""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "https://api.ipify.org"],
            capture_output=True, text=True, timeout=8
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None

def is_warp_available() -> bool:
    """Verifica si warp-cli está instalado y accesible en el PATH."""
    try:
        result = subprocess.run(
            ["warp-cli", "--version"],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def rotate_ip_warp(wait_seconds: int = 5) -> bool:
    global _last_rotation_time
    
    # Respetar cooldown mínimo entre rotaciones
    elapsed = time.time() - _last_rotation_time
    if elapsed < _MIN_ROTATION_COOLDOWN:
        logger.info(
            "Rotación omitida: cooldown activo (%.0fs restantes)", 
            _MIN_ROTATION_COOLDOWN - elapsed
        )
        return False
    
    if not is_warp_available():
        logger.warning("warp-cli no disponible en PATH. Rotación no posible.")
        return False
    
    ip_before = get_current_ip()
    logger.info(f"IP antes de rotación: {ip_before}")
    try:
        subprocess.run(["warp-cli", "disconnect"], capture_output=True, timeout=10)
        time.sleep(2)
        subprocess.run(["warp-cli", "connect"], capture_output=True, timeout=10)
        time.sleep(wait_seconds)
        ip_after = get_current_ip()
        logger.info(f"IP después de rotación: {ip_after}")
        if ip_after and ip_after != ip_before:
            logger.info("Rotación de IP exitosa.")
            _last_rotation_time = time.time()  # actualizar cooldown
            return True
        else:
            logger.warning("IP no cambió tras rotación WARP.")
            _last_rotation_time = time.time()  # evitar spam aunque falle
            return False
    except FileNotFoundError:
        logger.error("warp-cli no encontrado.")
        return False
    except Exception as e:
        logger.error(f"Error en rotate_ip_warp: {e}")
        return False

def connect_with_rotation(connect_fn, max_attempts: int = 3, rotate_on_fail: bool = True):
    """
    Wrapper para connect() que rota la IP ante rate limits.
    Uso:
      ok, msg = connect_with_rotation(api.connect)
    """
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Intento de conexion {attempt}/{max_attempts}")
        ok, msg = connect_fn()
        if ok:
            return ok, msg
        if rotate_on_fail and is_rate_limit_error(msg):
            logger.warning(f"Rate limit detectado: '{msg}'. Rotando IP WARP (intento {attempt})...")
            rotated = rotate_ip_warp(wait_seconds=8)
            if not rotated:
                logger.error("No se pudo rotar IP. Esperando 60s...")
                time.sleep(60)
        else:
            # Error no relacionado con rate limit
            return ok, msg
    return False, f"Fallidos {max_attempts} intentos con rotacion de IP"
