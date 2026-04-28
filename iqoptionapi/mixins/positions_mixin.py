import threading
from concurrent.futures import ThreadPoolExecutor
from iqoptionapi.logger import get_logger

class PositionsMixin:
    def get_open_positions(self, instrument_type=None, realtime_pnl=False):
        """
        SPRINT 7: Retorna posiciones abiertas.
        realtime_pnl=True: Usa position_changed_data para PnL dinámico.
        instrument_type: "forex" | "crypto" | "cfd" | "digital-option" | None
        """
        positions = []
        for pid, pos in self.positions_state_data.items():
            itype = pos.get("instrument_type")
            if instrument_type and itype != instrument_type:
                continue
            
            active_id = pos.get("active_id")
            pnl_estimate = None
            
            if realtime_pnl and hasattr(self.api, "position_changed_data") and pid in self.api.position_changed_data:
                pnl_estimate = self.api.position_changed_data[pid].get("pnl")
            
            # Fallback a estimación estática si no hay dato real-time
            if pnl_estimate is None:
                if hasattr(self.api, "current_prices") and active_id in self.api.current_prices:
                    current_price = self.api.current_prices[active_id]
                    open_price = pos.get("open_price")
                    direction = pos.get("direction")
                    if open_price and direction:
                        multiplier = 1 if direction == "buy" else -1
                        pnl_estimate = (current_price - open_price) / open_price * pos.get("margin", 0) * multiplier
            
            positions.append({
                "id": pid,
                "active_id": active_id,
                "instrument_type": itype,
                "direction": pos.get("direction"),
                "open_price": pos.get("open_price"),
                "margin": pos.get("margin"),
                "pnl_estimate": pnl_estimate,
                "raw": pos
            })
        return positions

    def monitor_positions(self, callback, interval=1.0):
        """
        SPRINT 5/8: Inicia monitoreo de posiciones.
        Evita fugas de memoria deteniendo hilos previos.
        """
        if hasattr(self, '_monitor_thread') and self._monitor_thread.is_alive():
            get_logger(__name__).warning("monitor_positions: ya existe un monitor activo. Re-iniciando...")
            self.stop_monitor_positions()
        
        self._monitor_stop = threading.Event()
        
        def monitor_loop():
            get_logger(__name__).info("Position monitoring started.")
            while not self._monitor_stop.wait(timeout=interval):
                try:
                    pos_list = self.get_open_positions()
                    callback(pos_list)
                except Exception as e:
                    get_logger(__name__).error("Monitor positions error: %s", e)

        self._monitor_thread = threading.Thread(target=monitor_loop, name="PositionMonitor", daemon=True)
        self._monitor_thread.start()

    def stop_monitor_positions(self):
        """Detiene el hilo de monitoreo."""
        if hasattr(self, "_monitor_stop"):
            self._monitor_stop.set()
            get_logger(__name__).info("Position monitoring stopped.")

    def close_all_positions(self, instrument_type=None, direction=None):
        """
        SPRINT 5: Cierra todas las posiciones que coincidan con los filtros.
        """
        positions = self.get_open_positions(instrument_type=instrument_type)
        if direction:
            positions = [p for p in positions if p["direction"] == direction]
        
        if not positions:
            return {"closed": [], "failed": []}
        
        get_logger(__name__).info(f"Closing {len(positions)} positions concurrently...")
        
        results = {"closed": [], "failed": []}
        
        def _close_one(pos):
            pid = pos["id"]
            # Detectar si es digital o margin
            if pos["instrument_type"] == "digital-option":
                check = self.close_digital_option(pid)
            else:
                check = self.close_position(pid)
            
            if check:
                return True, pid
            return False, pid

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(_close_one, p) for p in positions]
            for f in futures:
                success, pid = f.result()
                if success:
                    results["closed"].append(pid)
                else:
                    results["failed"].append(pid)
        
        return results

    def set_trailing_stop(self, position_id, distance_pips=None):
        """
        Sprint 5: Configura el Trailing Stop para una posición de margen.
        """
        get_logger(__name__).info(f"Setting trailing stop for position {position_id} (distance={distance_pips})")
        self.api.set_trailing_stop(position_id, distance_pips)
        return True

    def get_position_history(self, instrument_type="binary-option", from_date=None, to_date=None, limit=50):
        """
        SPRINT 7: Retorna historial de posiciones cerradas.
        """
        self.api.result = None
        self.api.result_event.clear()
        
        msg_body = {
            "instrument_type": instrument_type,
            "user_balance_id": self.api.balance_id,
            "limit": limit,
            "offset": 0
        }
        
        if from_date:
            if hasattr(from_date, 'timestamp'):
                from_date = int(from_date.timestamp())
            msg_body["start_time"] = from_date
            
        if to_date:
            if hasattr(to_date, 'timestamp'):
                to_date = int(to_date.timestamp())
            msg_body["end_time"] = to_date

        msg = {
            "name": "portfolio.get-history",
            "version": "2.0",
            "body": msg_body
        }

        self.api.send_websocket_request("sendMessage", msg)
        
        if self.api.result_event.wait(timeout=10):
            return self.api.result
        
        return None
