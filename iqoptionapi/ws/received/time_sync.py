import time

def time_sync(api, message):
    if message["name"] == "timeSync":
        api.timesync.server_timestamp = message["msg"]
        # SPRINT 6: Guardar timestamp local para calcular offset en tiempo real
        api._local_time_at_sync = time.time()
        # También guardar server_timestamp directamente en api para fácil acceso
        api.server_timestamp = message["msg"] / 1000
