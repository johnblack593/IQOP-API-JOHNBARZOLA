"""Module for IQ option websocket."""

def result(api, message):
    if message["name"] == "result":
        api.result = message["msg"]["success"]
        
        # S3: Si es una confirmación de compra, marcamos éxito
        if "request_id" in message:
            req_id = str(message["request_id"])
            if req_id in api.buy_multi_option:
                # Si aún no tenemos ID (vía option-opened), marcamos success: true
                # pero mantenemos el dict para que option-opened lo llene
                api.buy_multi_option[req_id]["success"] = message["msg"]["success"]

        ev = getattr(api, "result_event", None)
        if ev: ev.set()
