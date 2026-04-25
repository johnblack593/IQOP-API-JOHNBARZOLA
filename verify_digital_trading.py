import os
import time
import logging
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_verification():
    load_dotenv()
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    
    if not email or not password:
        logger.error("Credenciales no encontradas en .env")
        return

    logger.info("--- INICIANDO S4-T4: VALIDACIÓN LIVE DE DIGITAL TRADING ---")
    api = IQ_Option(email, password)
    api.connect()
    
    if not api.check_connect():
        logger.error("Fallo al conectar con IQ Option")
        return

    api.change_balance("PRACTICE")
    
    # 1. Descubrimiento de Activos
    logger.info("Buscando activos digitales abiertos...")
    open_times = api.get_all_open_time()
    digital_assets = [a for a, status in open_times['digital'].items() if status.get("open") == True]
    
    if not digital_assets:
        logger.error("No hay activos digitales abiertos en este momento.")
        api.api.close()
        return
    
    # Priorizar activos conocidos (Forex OTC suelen ser más estables para Digital)
    priority_assets = ["EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "EURJPY-OTC"]
    digital_assets.sort(key=lambda x: (x not in priority_assets, x))
    
    logger.info(f"Activos encontrados: {digital_assets[:20]}")
    
    # Seleccionar un activo
    target_asset = None
    for asset in digital_assets:
        # Intentar con y sin sufijos
        for suffix in ["", "-op"]:
            test_asset = asset + suffix if suffix and not asset.endswith("-op") else asset
            logger.info(f"Probando {test_asset}...")
            try:
                payout = api.get_digital_payout(test_asset)
                if payout > 0:
                    target_asset = test_asset
                    break
            except Exception as e:
                logger.warning(f"Error descubriendo payout para {test_asset}: {e}")
                # Fallback: Si es EURUSD-OTC y estamos en aprietos, lo intentamos directo
                if "EURUSD-OTC" in test_asset:
                    target_asset = test_asset
                    break
        if target_asset:
            break
            
    if not target_asset:
        if "EURUSD-OTC" in digital_assets:
            target_asset = "EURUSD-OTC"
            logger.info("Fallback: Forzando EURUSD-OTC para validación.")
        else:
            logger.error("No se encontró ningún activo digital con payout activo.")
            api.api.close()
            return

    logger.info(f"Activo seleccionado para validación: {target_asset}")

    # 2. Ejecución de Trade (CALL)
    amount = 1
    duration = 1 # 1 minuto
    action = "call"
    
    logger.info(f"Colocando orden Digital {action.upper()} en {target_asset} por ${amount}...")
    start_time = time.time()
    
    # Usamos buy_digital_spot_v2 que ahora está corregido para usar el protocolo V2
    check, order_id = api.buy_digital_spot_v2(target_asset, amount, action, duration)
    
    if check:
        logger.info(f"ORDEN EXITOSA. ID: {order_id}")
        
        # 3. Seguimiento y Captura de Resultado
        logger.info("Esperando resultado del trade (Timeout 120s)...")
        # check_win_v4 es reactivo y usa los eventos de portfolio.position-changed
        result = api.check_win_v4(order_id)
        
        duration_total = time.time() - start_time
        if result is not None:
            logger.info(f"RESULTADO CAPTURADO: {result}")
            logger.info(f"LATENCIA TOTAL: {duration_total:.2f}s")
            
            if duration_total < 120:
                logger.info("CERTIFICACIÓN S4-T4: PASSED")
            else:
                logger.warning("CERTIFICACIÓN S4-T4: WARNING (Latencia > 120s)")
        else:
            logger.error("ERROR: No se recibió el resultado del trade a tiempo.")
    else:
        logger.error(f"FALLO AL COLOCAR ORDEN: {order_id}")

    api.api.close()
    logger.info("--- FIN DE VALIDACIÓN ---")

if __name__ == "__main__":
    run_verification()
