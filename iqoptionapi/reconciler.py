"""
Reconciler: recupera resultados de trades que expiraron durante una desconexión.
Fuente primaria: HTTP betinfo (solo binary/turbo)
Fuente secundaria: WS position-history (todos los tipos)
"""
from iqoptionapi.core.logger import get_logger
import time


class Reconciler:
    def __init__(self, api_instance):
        """
        :param api_instance: IQ_Option (stable_api) instance
        """
        self._api = api_instance
        self._logger = get_logger(__name__)

    def reconcile(self, since_ts: float) -> dict:
        """
        Recupera resultados de trades desde since_ts hasta ahora.
        Retorna {order_id: "win" | "loose" | "equal" | "unknown"}

        Note: "loose" is the typo used by IQ Option servers — DO NOT correct it.
        """
        results = {}
        # Fuente 1: trade_journal — buscar trades con resultado None desde since_ts
        if hasattr(self._api, 'trade_journal'):
            pending = self._api.trade_journal.get_pending_since(since_ts)
            for order_id, trade_type in pending.items():
                result = self._try_betinfo(order_id)
                if result:
                    results[order_id] = result
                    continue
                result = self._try_position_history(order_id, since_ts)
                results[order_id] = result or "unknown"
        return results

    def _try_betinfo(self, order_id: int):
        """Try to get result via HTTP betinfo (binary/turbo only)."""
        try:
            success, data = self._api.get_betinfo(order_id)
            if success and data:
                return data.get("result")  # "win"/"loose"/"equal"
        except Exception as e:
            self._logger.debug("betinfo failed for %s: %s", order_id, e)
        return None

    def _try_position_history(self, order_id: int, since_ts: float):
        """WS position-history fallback for digital/CFD trades."""
        try:
            self._api.api.position_history_event.clear()
            self._api.api.send_websocket_request(
                name="sendMessage",
                msg={
                    "name": "portfolio.get-history-positions",
                    "version": "1.0",
                    "body": {
                        "user_balance_id": self._api.api.balance_id,
                        "start": int(since_ts),
                        "end": int(time.time()),
                        "limit": 50
                    }
                }
            )
            is_ready = self._api.api.position_history_event.wait(timeout=10.0)
            if is_ready:
                history = getattr(self._api.api, 'position_history_data', [])
                for pos in history:
                    if pos.get("external_id") == order_id or pos.get("id") == order_id:
                        close_profit = pos.get("close_profit", 0)
                        invest = pos.get("invest", 0)
                        if close_profit > invest:
                            return "win"
                        elif close_profit == invest:
                            return "equal"
                        else:
                            return "loose"  # IQ Option server typo — intentional
        except Exception as e:
            self._logger.debug("position_history failed for %s: %s", order_id, e)
        return None

