import inspect
import threading
from iqoptionapi.api import IQOptionAPI

api = IQOptionAPI.__new__(IQOptionAPI)
api.__init__("iqoption.com", "test@test.com")

print("=== Events declarados en api.py ===")
events = []
for name in sorted(dir(api)):
    val = getattr(api, name, None)
    if isinstance(val, threading.Event):
        events.append(name)
        print(f"  {name}")

print(f"\nTotal events: {len(events)}")
