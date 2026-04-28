import os
import json
import time
import datetime
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

def reconstruct_digital_id(asset_id, expiration_timestamp, duration_min, direction):
    # pattern: do{asset_id}A{YYYYMMDD}D{HHMMSS}T{min}M{dir}SPT
    dt = datetime.datetime.fromtimestamp(expiration_timestamp, tz=datetime.timezone.utc)
    date_str = dt.strftime("%Y%m%d")
    time_str = dt.strftime("%H%M%S")
    
    dir_code = "C" if direction.lower() in ["call", "sube", "up"] else "P"
    duration_code = f"T{duration_min}M"
    
    return f"do{asset_id}A{date_str}D{time_str}{duration_code}{dir_code}SPT"

print("=== TEST RECONSTRUCCION DIGITALPattern ===")
api = IQ_Option(email, password)
check, reason = api.connect()
if not check:
    print(f"Failed to connect: {reason}")
    exit(1)

api.change_balance("PRACTICE")

# Activo: EURUSD-OTC (ID 76 para KYC)
asset = "EURUSD-OTC"
asset_id = 76 

# 1. Obtener expiraciones proximas
# Para digital de 1 min, es el siguiente minuto redondo
now = api.get_server_timestamp()
expiration = (now // 60 + 1) * 60
print(f"Server time: {datetime.datetime.fromtimestamp(now, tz=datetime.timezone.utc)}")
print(f"Target Expiration: {datetime.datetime.fromtimestamp(expiration, tz=datetime.timezone.utc)}")

# 2. Reconstruir ID
instrument_id = reconstruct_digital_id(asset_id, expiration, 1, "call")
print(f"Generated Instrument ID: {instrument_id}")

# 3. Intentar compra manual vía WS directo (para validar patron)
# El SDK tiene place_digital_option pero queremos ver si este ID funciona
print("Enviando orden de prueba...")
# Usamos el metodo interno para enviar el mensaje exacto que vimos en el browser
msg = {
    "name": "digital-options.place-digital-option",
    "version": "3.0",
    "body": {
        "user_balance_id": api.get_balance_id(),
        "instrument_id": instrument_id,
        "amount": "1",
        "instrument_index": int(time.time()), # placeholder
        "asset_id": asset_id
    }
}

# Enviamos y esperamos respuesta
request_id = "test_manual_digital"
api.api.send_websocket_request(name="sendMessage", msg=msg, request_id=request_id)

# Nota: El SDK podria no tener un handler para la respuesta de este mensaje especifico
# pero el servidor deberia aceptar la orden si el ID es correcto.
# Vamos a ver que pasa en el log.
time.sleep(3)
print("Consultando posiciones digitales...")
positions = api.get_positions("digital-option")
print(f"Posiciones encontradas: {json.dumps(positions, indent=2)}")

api.close()
