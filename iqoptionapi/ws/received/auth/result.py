"""Module for IQ option websocket."""

def result(api, message):
    if message["name"] == "result":
        api.result = message["msg"]["success"]
        
        # S3: Si es una confirmación de compra, marcamos éxito
        if "request_id" in message:
            req_id = str(message["request_id"])
            if req_id in api.buy_multi_option:
                # Si aún no tenemos ID (vía option-opened), marcamos success
                api.buy_multi_option[req_id]["success"] = message["msg"]["success"]
            
            # S4-T3: Si falló la apertura, eliminamos de la cola de correlación
            if not message["msg"]["success"]:
                api.remove_pending_buy_id(req_id)

        ev = getattr(api, "result_event", None)
        if ev: ev.set()
