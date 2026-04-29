"""
JCBV-NEXUS SDK v9.1.000 — Example 04: Real-Time Candle Stream
Recibe 5 velas de EURUSD en tiempo real y termina.
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
    print(f"Falló la conexión: {reason}"); exit(1)

active = "EURUSD"
size = 60 # 1 minuto

api.start_candles_one_stream(active, size)
print(f"Stream iniciado para {active} ({size}s). Esperando velas...")

seen = set()
timeout = time.time() + 60 # Máximo 1 minuto de espera

while time.time() < timeout:
    candles = api.get_realtime_candles(active, size)
    new = {k: v for k, v in candles.items() if k not in seen}
    for ts, candle in sorted(new.items()):
        print(f"  Vela {ts}: O={candle['open']:.5f} "
              f"C={candle['close']:.5f} "
              f"H={candle['max']:.5f} L={candle['min']:.5f}")
        seen.add(ts)
    if len(seen) >= 5:
        break
    time.sleep(1)

api.stop_candles_one_stream(active, size)
print(f"Stream detenido. Velas recibidas: {len(seen)}")
api.disconnect()
