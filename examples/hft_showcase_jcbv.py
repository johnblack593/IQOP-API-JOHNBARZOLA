import sys
import os
import time
import logging

# Ensure iqoptionapi can be imported from the root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def hft_showcase():
    logging.info("Iniciando IQ Option API - HFT Showcase (JCBV Edition)")
    
    # 1. Autenticación Instintiva
    email = os.environ.get("IQ_EMAIL", "TU_CORREO_AQUI")
    password = os.environ.get("IQ_PASSWORD", "TU_PASSWORD_AQUI")
    
    if email == "TU_CORREO_AQUI":
        logging.error("Por favor configura tus variables de entorno IQ_EMAIL e IQ_PASSWORD antes de ejecutar.")
        return

    api = IQ_Option(email, password)
    check, reason = api.connect()
    if not check:
        logging.error(f"Error de conexión: {reason}")
        return
        
    logging.info("✅ Conexión establecida correctamente. Cambiando a cuenta PRACTICE.")
    api.change_balance("PRACTICE")
    
    # ===================================================================
    # FEATURE 1: Control de Horarios Geográficos (Market Schedules)
    # ===================================================================
    logging.info("--- FEATURE 1: ESCANEO DE MERCADOS Y HORARIOS ---")
    open_markets = api.get_all_open_time()
    
    asset_to_trade = "EURUSD"
    market_type = "turbo"
    
    # Automáticamente cambiamos a OTC si es fin de semana y el normal está cerrado
    if not open_markets.get(market_type, {}).get(asset_to_trade, {}).get("open", False):
        logging.warning(f"⚠️ {asset_to_trade} se encuentra CERRADO actualmente en opciones {market_type}.")
        asset_to_trade = "EURUSD-OTC"
        logging.info(f"🔄 Cambiando dinámicamente al mercado OTC: {asset_to_trade}")
    
    is_open = open_markets.get(market_type, {}).get(asset_to_trade, {}).get("open", False)
    logging.info(f"📊 Estado del Activo {asset_to_trade} [{market_type}]: {'ABIERTO' if is_open else 'CERRADO'}")
    
    if not is_open:
        logging.error("El activo seleccionado no está disponible. Abortando demo.")
        return

    # ===================================================================
    # FEATURE 2: Control de Temporalidad Avanzada (Expiración Exacta)
    # ===================================================================
    logging.info("--- FEATURE 2: EJECUCIÓN CON DURACIÓN CONTROLADA ---")
    investment_amount = 1.0  # $1
    direction = "call"       # 'call' o 'put'
    duration_minutes = 1     # El usuario decide la temporalidad (1m, 5m, 15m)
    
    logging.info(f"🚀 Ejecutando Trade HFT: {direction.upper()} | {investment_amount}$ | Activo: {asset_to_trade} | Duración: {duration_minutes} min")
    # El 4to parámetro es la duración; la API sincroniza esto con el backend usando `expiration.py`
    check_buy, order_id = api.buy(investment_amount, asset_to_trade, direction, duration_minutes)
    
    if not check_buy:
        logging.error(f"❌ Falló la orden de compra. Detalles: {order_id}")
        return
        
    logging.info(f"✅ ¡Trade Ejecutado al milisegundo! ID de Rastreo: {order_id}")
    
    # ===================================================================
    # FEATURE 3: Sistema Asíncrono de Cierre y Verificación P&L (Profit & Loss)
    # ===================================================================
    logging.info("--- FEATURE 3: TRACKING DE RESULTADOS Y PROFIT/LOSS ---")
    logging.info(f"⏳ Esperando que la operación de {duration_minutes} minuto(s) expire naturalmente en el servidor...")
    
    # check_win_v4 fue blindado en JCBV Edition con un timeout interno seguro contra cuelgues (120mins de tolerancia).
    # Se queda escuchando los eventos de websockets de forma ultraligera sin colgar tu CPU (GIL seguro).
    resultado_texto, profit_exacto = api.check_win_v4(order_id)
    
    if resultado_texto is None:
        logging.error("⚠️ La operación expiró en timeout o se desconectó la red durante la espera.")
    else:
        logging.info("==================================================")
        logging.info("🏆 RESULTADO FINAL DEL TRADE EXTRAÍDO DEL BROKER")
        
        if resultado_texto == "win":
            logging.info(f"🟢 [GANADO] Rendimiento Obtenido: +${profit_exacto:.2f}")
        elif resultado_texto == "loose":
            logging.info(f"🔴 [PERDIDO] Pérdida Registrada: ${profit_exacto:.2f}")
        else:
            logging.info(f"⚪ [EMPATE] Capital devuelto: ${profit_exacto:.2f}")
        
        logging.info("==================================================")

if __name__ == '__main__':
    hft_showcase()
