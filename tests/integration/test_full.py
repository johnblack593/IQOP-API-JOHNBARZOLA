import os
import sys
import time

# Path setup
sys.path.append("d:/Programacion/API-IQ/IQOP-API-JOHNBARZOLA")

def load_env():
    env_path = 'd:/Programacion/API-IQ/IQOP-API-JOHNBARZOLA/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

def main():
    load_env()
    from iqoptionapi.stable_api import IQ_Option
    
    email = os.environ.get('IQ_EMAIL')
    password = os.environ.get('IQ_PASSWORD')
    
    if not email or not password:
        print("ANOMALIA: Credenciales no encontradas")
        sys.exit(1)
        
    print(f"Intentando conexion con: {email}")
    iq = IQ_Option(email, password)
    check, reason = iq.connect()
    
    if not check:
        print(f"ANOMALIA: Conexion fallida: {reason}")
        sys.exit(1)
        
    print("OK: Conexion exitosa")
    print(f"  Balance practice ID: {iq.get_balance_id()}")

    # Paso 2.2 - Balance y cuenta
    print("--- Paso 2.2: Verificacion de balance ---")
    iq.change_balance("PRACTICE")
    balance = iq.get_balance()
    print(f"OK: Balance PRACTICE: {balance}")
    if not (isinstance(balance, (int, float)) and balance >= 0):
        print("ANOMALIA: Balance invalido")
        sys.exit(1)

    # Paso 2.3 - Activos disponibles (candles stream)
    print("--- Paso 2.3: Verificacion de activos (candles) ---")
    status = iq.start_candles_one_stream("EURUSD", 60)
    print(f"  Stream status: {status}")
    time.sleep(5)
    candles = iq.get_realtime_candles("EURUSD", 60)

    if candles is None or len(candles) == 0:
        print("ADVERTENCIA: candles retorno None o vacio - verificar stream")
    else:
        print(f"OK: Candle stream OK: {len(candles)} velas recibidas")

    iq.stop_candles_one_stream("EURUSD", 60)
    
    # Paso 2.4 - Operacion Binary
    print("--- Paso 2.4: Verificacion Operacion Binary ---")
    check_buy, order_id = iq.buy(1, "EURUSD", "call", 1)
    if not check_buy:
        print(f"ADVERTENCIA: buy() retorno False. order_id={order_id}")
    else:
        print(f"OK: Orden colocada: order_id={order_id}")
        t_start = time.time()
        result = iq.check_win_v4(order_id)
        elapsed = time.time() - t_start
        print(f"  Tiempo de espera: {elapsed:.1f}s")
        if result is None:
            print("OK: check_win_v4 retorno None (timeout esperado en Sprint 0/1)")
        else:
            print(f"OK: Resultado recibido: {result}")
        
        if elapsed >= 130:
            print(f"ANOMALIA CRITICA: check_win_v4 se colgo por {elapsed:.1f}s")
            sys.exit(1)

    # Paso 2.5 - Operacion Digital
    print("--- Paso 2.5: Verificacion Operacion Digital ---")
    check_dig, digital_order_id = iq.buy_digital_spot("EURUSD", 1, "call", 1)
    if not check_dig:
        print(f"ADVERTENCIA: buy_digital_spot() retorno False: {digital_order_id}")
    else:
        print(f"OK: Digital order colocada: order_id={digital_order_id}")
        t_start = time.time()
        result_dig = iq.check_win_digital_v2(digital_order_id)
        elapsed_dig = time.time() - t_start
        print(f"  Tiempo de espera: {elapsed_dig:.1f}s")
        print(f"OK: check_win_digital_v2 retorno: {result_dig}")
        if elapsed_dig >= 130:
            print(f"ANOMALIA: check_win_digital_v2 se colgo {elapsed_dig:.1f}s")
            sys.exit(1)

if __name__ == "__main__":
    main()
