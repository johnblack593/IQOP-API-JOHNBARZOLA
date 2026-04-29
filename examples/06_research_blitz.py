# ─────────────────────────────────────────────────────────────
# JCBV-NEXUS SDK v9.1.000 — Example Script
# Este archivo es un ejemplo funcional, NO un test de pytest.
# Requiere: .env con IQ_EMAIL y IQ_PASSWORD
# Uso: python examples/06_research_blitz.py
# ─────────────────────────────────────────────────────────────
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from iqoptionapi.stable_api import IQ_Option
import iqoptionapi.core.constants as OP_code

api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
api.connect()
api.change_balance("PRACTICE")

blitz = api.get_blitz_instruments()
binary = api.get_all_init_v2().get("result", {}).get("turbo", {}).get("actives", {})

print(f"Blitz assets: {len(blitz)}")
print(f"Binary Turbo assets: {len(binary)}")

cross = []
for name, data in blitz.items():
    if name in binary:
        cross.append(name)

print(f"\nBlitz assets also in Binary Turbo: {len(cross)}")
print(f"Sample cross entries: {cross[:10]}")

# Check SOLUSD-OTC and LTCUSD-OTC
for asset in ["SOLUSD-OTC", "LTCUSD-OTC", "EURUSD-op", "EURUSD-OTC"]:
    print(f"\n{asset}:")
    print(f"  In Blitz: {asset in blitz}")
    print(f"  In Binary: {asset in binary}")
    print(f"  In OP_code.ACTIVES: {asset in OP_code.ACTIVES}")
    if asset in OP_code.ACTIVES:
        print(f"    ID: {OP_code.ACTIVES[asset]}")

api.close()

