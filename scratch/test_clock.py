from iqoptionapi.time_sync import _clock
import time
print(f"Clock offset: {_clock.offset_seconds()}")
_clock.update(int(time.time() * 1000) + 5000) # Simular 5s offset
print(f"Clock offset after update: {_clock.offset_seconds()}")
print(f"Clock now: {_clock.now()}")
