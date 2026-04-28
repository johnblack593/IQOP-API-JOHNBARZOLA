"""
Handler for margin order placement results.

The server responds to marginal-{type}.place-market-order with:
  name: "market-order-placed"
  msg: {"id": 101093577852}
  status: 2000

This handler captures the order ID and signals the margin_order_event.
"""
from iqoptionapi.logger import get_logger

logger = get_logger(__name__)


def margin_order_result(api, message):
    """
    Called by the WS router when a 'market-order-placed' message arrives.
    
    Server response format:
        {
            "request_id": "",
            "name": "market-order-placed",
            "msg": {"id": 101093577852},
            "status": 2000
        }
    """
    if message.get("name") == "market-order-placed":
        msg = message.get("msg", {})
        status = message.get("status")
        
        if status == 2000:
            order_id = msg.get("id")
            api.margin_order_result = {
                "id": order_id,
                "status": status,
                "raw": message,
            }
            logger.info(
                "Margin order placed: id=%s status=%s",
                order_id, status
            )
        else:
            api.margin_order_result = {
                "id": None,
                "status": status,
                "error": msg,
                "raw": message,
            }
            logger.warning(
                "Margin order failed: status=%s msg=%s",
                status, msg
            )

        if hasattr(api, "margin_order_event"):
            api.margin_order_event.set()
