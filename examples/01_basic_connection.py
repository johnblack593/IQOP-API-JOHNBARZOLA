"""
JCBV-NEXUS SDK v9.1.000 — Example 01: Basic Connection
Verifica la conexión, imprime el balance y desconecta.
Requiere: .env con IQ_EMAIL y IQ_PASSWORD
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
print("Connecting...")
status, reason = api.connect()

if not status:
    print(f"Connection failed: {reason}")
    exit(1)

print(f"Connected: {status}")
api.change_balance("PRACTICE")

balance = api.get_balance()
print(f"Balance: {balance:.2f} USD (PRACTICE)")

# profile asynchrony handled internally by stable_api
profile = api.get_profile_ansyc()
print(f"Account ID: {profile.get('id', 'N/A')}")

api.disconnect()
print("Disconnected.")
