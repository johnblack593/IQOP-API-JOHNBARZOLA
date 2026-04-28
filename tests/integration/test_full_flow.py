"""
Test de flujo completo JCBV-NEXUS SDK — Sprint 7
Ejecutar con: python scratch/test_full_flow.py
Requiere: EMAIL y PASSWORD en variables de entorno
"""
import os
import time
import logging
from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("test_flow")

EMAIL = os.environ.get("IQ_EMAIL", "your_email")
PASSWORD = os.environ.get("IQ_PASSWORD", "your_password")

def test_all():
    api = IQ_Option(EMAIL, PASSWORD)
    
    logger.info("T1: Conectando y verificando sincronización...")
    status, reason = api.connect()
    if not status:
        logger.error(f"Error de conexión: {reason}")
        return
    
    api.change_balance("PRACTICE")
    logger.info(f"Conexión exitosa. Balance actual: {api.get_balance()}")

    logger.info("T2: Probando stream de velas EURUSD 1m...")
    active = "EURUSD"
    api.start_candles_stream(active, 60, 1)
    time.sleep(5)
    candles = api.get_realtime_candles(active, 60)
    if candles:
        logger.info(f"Velas recibidas: {len(candles)}")
    else:
        logger.warning("No se recibieron velas.")

    logger.info("T3: Prueba de compra binaria (Demo)...")
    # Nota: Descomentar para probar ejecución real en demo
    # status, buy_id = api.buy(1, active, "call", 1)
    # if status:
    #     logger.info(f"Compra ejecutada: {buy_id}. Esperando resultado...")
    #     print(api.check_win_v3(buy_id))

    logger.info("T6: Verificando get_open_positions(realtime_pnl=True)...")
    positions = api.get_open_positions(realtime_pnl=True)
    logger.info(f"Posiciones abiertas detectadas: {len(positions)}")

    logger.info("T7: Verificando short_active_info...")
    active_id = api.get_active_id_by_name(active)
    info = api.get_short_active_info(active_id)
    if info:
        logger.info(f"Short active info para {active}: {info}")
    else:
        logger.warning(f"No se obtuvo short_active_info para {active}")

    logger.info("Pruebas finalizadas.")
    api.close()

if __name__ == "__main__":
    test_all()
