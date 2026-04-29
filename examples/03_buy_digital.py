"""
JCBV-NEXUS SDK v9.1.000 — Example 03: Buy Digital + Check Win
"""
import os
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

active = "EURUSD"
amount = 1
action = "call"
duration = 1

print(f"Comprando Digital {action} en {active}, ${amount}, {duration}m...")
success, order_id = api.buy_digital_spot(
    active=active,
    amount=amount,
    action=action,
    duration=duration
)

if success:
    print(f"Digital order: {order_id}")
    print("Esperando resultado (máx. 90s)...")
    # Sprint 14: check_win_digital reactivo
    result = api.check_win_digital(order_id, timeout=90)
    print(f"Resultado: {result}")
else:
    print(f"buy_digital_spot falló: {order_id}")

api.disconnect()
