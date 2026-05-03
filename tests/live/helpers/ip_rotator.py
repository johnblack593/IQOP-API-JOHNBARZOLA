import subprocess
import time
import logging

def rotate_ip():
    """
    Rotates IP using Cloudflare WARP CLI.
    """
    logger = logging.getLogger("IPRotator")
    logger.info("🔄 Solicitando rotación de IP vía Cloudflare WARP...")
    
    try:
        # 1. Desconectar
        subprocess.run(["warp-cli", "disconnect"], capture_output=True, check=True)
        time.sleep(2)
        
        # 2. Conectar (esto suele asignar una nueva IP de salida)
        subprocess.run(["warp-cli", "connect"], capture_output=True, check=True)
        
        # 3. Esperar a que se estabilice
        for _ in range(10):
            res = subprocess.run(["warp-cli", "status"], capture_output=True, text=True)
            if "Status update: Connected" in res.stdout:
                logger.info("✅ IP rotada y conexión WARP restablecida.")
                time.sleep(2) # Margen extra
                return True
            time.sleep(1)
            
        logger.warning("⚠️ WARP tardó demasiado en reconectar.")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error al rotar IP: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rotate_ip()
