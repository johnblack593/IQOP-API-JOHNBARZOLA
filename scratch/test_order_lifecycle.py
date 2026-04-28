import time
import logging
import sys
import os

# Añadir el path del SDK
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from iqoptionapi.stable_api import IQ_Option
import iqoptionapi.config as config

# Configuración de logging para ver los handlers en acción
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def test_lifecycle():
    # USAR CREDENCIALES DEL ENTORNO O PLACEHOLDERS
    email = os.getenv("IQ_EMAIL", "tu_email@gmail.com")
    password = os.getenv("IQ_PASS", "tu_password")
    
    print(f"Iniciando sesión como {email}...")
    I_api = IQ_Option(email, password)
    check, reason = I_api.connect()
    
    if not check:
        print(f"Error de conexión: {reason}")
        return

    I_api.change_balance("PRACTICE")
    
    active = "EURUSD"
    print(f"\n--- Probando Lifecycle en {active} ---")
    
    # 1. Obtener balance marginal inicial
    balance = I_api.get_marginal_balance("forex")
    print(f"Balance marginal inicial (forex): {balance}")
    
    # 2. Colocar orden pendiente (Stop Order)
    # Precio actual + algo para que no se ejecute de inmediato
    current_price = I_api.get_candles(active, 60, 1, time.time())[0]["close"]
    stop_price = current_price + 0.0010  # 10 pips arriba
    
    print(f"Colocando orden pendiente en {stop_price}...")
    status, order_id = I_api.place_pending_order(
        active=active,
        instrument_type="forex",
        side="buy",
        amount=10,
        leverage=1000,
        stop_price=stop_price,
        take_profit=10,
        stop_loss=-5
    )
    
    if status:
        print(f"Orden pendiente colocada exitosamente! ID: {order_id}")
        
        # 3. Verificar en la lista de pendientes
        print("Consultando órdenes pendientes...")
        pending = I_api.get_pending_orders("forex")
        if order_id in pending:
            print(f"Confirmado: La orden {order_id} está en el event store.")
        else:
            print(f"Error: La orden {order_id} NO se encuentra en el store local.")
            
        # 4. Cancelar la orden
        print(f"Cancelando orden {order_id}...")
        canceled = I_api.cancel_pending_order(order_id)
        if canceled:
            print("Orden cancelada exitosamente!")
        else:
            print("Fallo al cancelar la orden (timeout).")
            
    else:
        print(f"Error al colocar orden: {order_id}")
        
    I_api.api.close()
    print("\n--- Test Finalizado ---")

if __name__ == "__main__":
    test_lifecycle()
