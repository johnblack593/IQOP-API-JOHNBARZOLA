import time
from iqoptionapi.core.time_sync import _clock

def time_sync(api, message):
    if message["name"] == "timeSync":
        api.timesync.server_timestamp = message["msg"]
        
        # SPRINT 7: Actualizar el singleton global de sincronización
        _clock.update(message["msg"])
        
        # Backward compatibility para Sprint 6
        api._local_time_at_sync = time.time()
        api.server_timestamp = message["msg"] / 1000

