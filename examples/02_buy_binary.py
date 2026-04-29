"""
JCBV-NEXUS SDK v9.1.000 — Example 02: Buy Binary + Check Win
Ejecuta una operación binaria en EURUSD y espera el resultado.
Usa cuenta PRACTICE — seguro para pruebas.
"""
import os, time
from pathlib import Path
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

# Load .env from root
load_dotenv(Path(__file__).parent.parent / ".env")

EMAIL    = os.environ.get("IQ_EMAIL")
PASSWORD = os.environ.get("IQ_PASSWORD")

if not EMAIL or not PASSWORD:
    print("Error: IQ_EMAIL or IQ_PASSWORD not found in .env file")
    exit(1)

api = IQ_Option(EMAIL, PASSWORD)
status, reason = api.connect()
if not status:
    print(f"Falló la conexión: {reason}")
    exit(1)

api.change_balance("PRACTICE")
print(f"Balance inicial: {api.get_balance():.2f}")

# Verificar que EURUSD está abierto
all_open = api.get_all_open_time()
if not all_open.get("binary", {}).get("EURUSD", {}).get("open"):
    print("EURUSD no está disponible ahora. Intentar en horario de mercado o usar OTC.")
    api.disconnect()
    exit(0)

# Ejecutar operación
amount    = 1       # USD
asset     = "EURUSD"
direction = "call"  # "call" = sube, "put" = baja
duration  = 1       # minutos

print(f"Comprando {direction} en {asset}, ${amount}, {duration}m...")
success, order_id = api.buy(amount, asset, direction, duration)

if not success:
    print(f"buy() falló. order_id={order_id}")
    api.disconnect()
    exit(1)

print(f"Orden ejecutada: {order_id}")
print("Esperando resultado (máx. 90s)...")

# Sprint 14: check_win es ahora reactivo y no bloquea el hilo principal
result = api.check_win(order_id, timeout=90)

if result is None:
    print("Timeout — resultado no recibido en 90 segundos.")
else:
    emoji = "✅" if result == "win" else "❌"
    print(f"{emoji} Resultado: {result.upper()}")

print(f"Balance final: {api.get_balance():.2f}")
api.disconnect()
