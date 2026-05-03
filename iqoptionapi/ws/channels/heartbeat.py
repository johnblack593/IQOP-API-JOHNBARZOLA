from iqoptionapi.ws.channels.base import Base
class Heartbeat(Base):
    name = "heartbeat"
    
    def __call__(self, heartbeatTime):  
        # S15-T1: Actualizar timestamp para evitar que el watchdog fuerce reconexión
        if hasattr(self.api, "_last_heartbeat"):
            self.api._last_heartbeat = __import__('time').time()
            
        data = {
            "msg": {
                "heartbeatTime": int(heartbeatTime),
                "userTime": int(self.api.timesync.server_timestamp * 1000)
            }
        }
        self.send_websocket_request(self.name, data, no_force_send=False)
