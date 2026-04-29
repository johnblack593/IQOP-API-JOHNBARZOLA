import threading
import time
from concurrent.futures import ThreadPoolExecutor
from iqoptionapi.core.logger import get_logger
import iqoptionapi.core.config as config

from iqoptionapi.core.ratelimit import rate_limited

class PositionsMixin:
    def get_open_positions(self, instrument_type=None, realtime_pnl=False):
        """
        SPRINT 7: Retorna posiciones abiertas locales.
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

    # --- Métodos migrados de stable_api.py ---

    def get_positions(self, instrument_type):
        self.api.positions_event.clear()
        self.api.get_positions(instrument_type)
        is_ready = self.api.positions_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for positions")
            return False, None
        
        if self.api.positions.get("status") == 2000:
            return True, self.api.positions["msg"]
        else:
            return False, None

    def get_position(self, position_id):
        self.api.position_event.clear()
        self.api.get_position(position_id)
        is_ready = self.api.position_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for position")
            return False, None
        
        if self.api.position.get("status") == 2000:
            return True, self.api.position["msg"]
        else:
            return False, None

    def get_digital_position_by_position_id(self, position_id):
        self.api.position_event.clear()
        self.api.get_digital_position(position_id)
        is_ready = self.api.position_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for digital position")
            return False, None
        return True, self.api.position

    def get_digital_position(self, order_id):
        self.api.digital_position_event.clear()
        self.api.get_digital_position(order_id)
        is_ready = self.api.digital_position_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for digital position")
            return False, None
        return True, self.api.digital_position

    def get_position_history_v2(self, instrument_type, limit, offset, start, end):
        self.api.position_history_v2_event.clear()
        self.api.get_position_history_v2(instrument_type, limit, offset, start, end)
        is_ready = self.api.position_history_v2_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for position history v2")
            return False, None
        
        if self.api.position_history_v2.get("status") == 2000:
            return True, self.api.position_history_v2["msg"]
        else:
            return False, None

    def get_available_leverages(self, instrument_type, actives_id):
        self.api.available_leverages_event.clear()
        self.api.get_available_leverages(instrument_type, actives_id)
        is_ready = self.api.available_leverages_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for available leverages")
            return False, None
        
        if self.api.available_leverages.get("status") == 2000:
            return True, self.api.available_leverages["msg"]
        else:
            return False, None

    def get_overnight_fee(self, instrument_type, actives_id):
        self.api.overnight_fee_event.clear()
        self.api.get_overnight_fee(instrument_type, actives_id)
        is_ready = self.api.overnight_fee_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for overnight fee")
            return False, None
        
        if self.api.overnight_fee.get("status") == 2000:
            return True, self.api.overnight_fee["msg"]
        else:
            return dict(self.api.overnight_fee.msg)

    @rate_limited("_order_bucket", on_limit=False)
    def close_position(self, position_id):
        self.api.close_position_event.clear()
        self.api.close_position(position_id)
        is_ready = self.api.close_position_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for close position")
            return False
        return self.api.close_position_data.get("status") == 2000

    def close_position_v2(self, position_id):
        self.api.close_position_event.clear()
        self.api.close_position(position_id)
        is_ready = self.api.close_position_event.wait(timeout=config.TIMEOUT_WS_DATA)
        if not is_ready:
            get_logger(__name__).warning("Timeout waiting for close position v2")
            return False
        return True

    def get_all_open_positions(self, timeout: float = 10.0) -> dict:
        """
        Retorna dict con posiciones abiertas por tipo de instrumento.
        Llama en paralelo los 4 tipos para minimizar latencia.
        """
        import concurrent.futures
        instrument_types = ["binary-option", "turbo-option", "digital-option", "blitz"]
        result = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.get_positions, itype): itype
                for itype in instrument_types
            }
            for future in concurrent.futures.as_completed(futures):
                itype = futures[future]
                try:
                    success, data = future.result()
                    result[itype] = data if success else []
                except Exception as e:
                    get_logger(__name__).error("get_all_open_positions error for %s: %s", itype, e)
                    result[itype] = []
        return result

    def close_margin_position(self, order_id, timeout=15.0):
        '\n        Closes a margin position by its order ID.\n\n        '
        (position_id, m_type) = self._resolve_margin_position_id(order_id)
        get_logger(__name__).info('Closing margin position: id=%s (type=%s)', position_id, m_type)
        self.api.close_position_data = None
        self.api.close_position_data_event.clear()
        data = {'name': f'marginal-{m_type}.close-position', 'version': '1.0', 'body': {'position_id': int(position_id)}}
        self.api.send_websocket_request('sendMessage', data)
        start_t = time.time()
        while ((self.api.close_position_data is None) and ((time.time() - start_t) < timeout)):
            self.api.close_position_data_event.wait(timeout=1)
            self.api.close_position_data_event.clear()
        if (self.api.close_position_data is not None):
            status = self.api.close_position_data.get('status')
            if (status == 2000):
                get_logger(__name__).info('Margin position closed: %s', position_id)
                return (True, self.api.close_position_data)
            else:
                return (False, f'SERVER_ERROR: status={status}')
        return (False, f'TIMEOUT after {timeout}s')

    def get_margin_positions(self, instrument_type='forex'):
        '\n        Gets all open margin positions for a given instrument type.\n\n        Args:\n            instrument_type: "forex", "cfd", or "crypto"\n\n        Returns:\n            list of position dicts, or empty list on error\n        '
        full_type = self._MARGIN_TYPE_MAP.get(instrument_type.lower(), instrument_type)
        return self.get_open_positions(instrument_type=full_type)

    def _resolve_margin_position_id(self, order_id):
        try:
            for m_type in ['marginal-forex', 'marginal-cfd', 'marginal-crypto']:
                positions = self.get_open_positions(instrument_type=m_type)
                for pos in positions:
                    pos_id = pos.get('id')
                    ext_id = pos.get('external_id')
                    order_ids = []
                    raw_event = pos.get('raw_event', {})
                    for (k, v) in raw_event.items():
                        if (isinstance(v, dict) and ('order_ids' in v)):
                            order_ids.extend(v['order_ids'])
                    if ((str(order_id) == str(ext_id)) or (order_id in order_ids) or (str(order_id) in [str(o) for o in order_ids])):
                        actual_id = (ext_id if (ext_id is not None) else pos_id)
                        m_prefix = m_type.replace('marginal-', '')
                        return (actual_id, m_prefix)
        except Exception as e:
            get_logger(__name__).warning('Portfolio search failed: %s', e)
        return (order_id, 'forex')

    def get_digital_current_profit(self, ACTIVE, duration):
        profit = self.api.instrument_quotes_generated_data[ACTIVE][(duration * 60)]
        for key in profit:
            if (key.find('SPT') != (- 1)):
                return profit[key]
        return False

    @rate_limited('_order_bucket')
    def get_digital_spot_profit_after_sale(self, position_id):

        def get_instrument_id_to_bid(data, instrument_id):
            for row in data['msg']['quotes']:
                if (row['symbols'][0] == instrument_id):
                    return row['price']['bid']
            return None
        start_t = time.time()
        while ((self.get_async_order(position_id).get('position-changed') == {}) and ((time.time() - start_t) < 15.0)):
            self.api.position_changed_event.wait(timeout=1)
            self.api.position_changed_event.clear()
        position = self.get_async_order(position_id)['position-changed']['msg']
        if ('MPSPT' in position['instrument_id']):
            z = False
        elif ('MCSPT' in position['instrument_id']):
            z = True
        else:
            get_logger(__name__).error(('get_digital_spot_profit_after_sale position error' + str(position['instrument_id'])))
        ACTIVES = position['raw_event']['instrument_underlying']
        amount = max(position['raw_event']['buy_amount'], position['raw_event']['sell_amount'])
        start_duration = (position['instrument_id'].find('PT') + 2)
        end_duration = (start_duration + position['instrument_id'][start_duration:].find('M'))
        duration = int(position['instrument_id'][start_duration:end_duration])
        z2 = False
        getAbsCount = position['raw_event']['count']
        instrumentStrikeValue = (position['raw_event']['instrument_strike_value'] / 1000000.0)
        spotLowerInstrumentStrike = (position['raw_event']['extra_data']['lower_instrument_strike'] / 1000000.0)
        spotUpperInstrumentStrike = (position['raw_event']['extra_data']['upper_instrument_strike'] / 1000000.0)
        aVar = position['raw_event']['extra_data']['lower_instrument_id']
        aVar2 = position['raw_event']['extra_data']['upper_instrument_id']
        getRate = position['raw_event']['currency_rate']
        instrument_quotes_generated_data = self.get_instrument_quotes_generated_data(ACTIVES, duration)
        f_tmp = get_instrument_id_to_bid(instrument_quotes_generated_data, aVar)
        if (f_tmp != None):
            self.get_digital_spot_profit_after_sale_data[position_id]['f'] = f_tmp
            f = f_tmp
        else:
            f = self.get_digital_spot_profit_after_sale_data[position_id]['f']
        f2_tmp = get_instrument_id_to_bid(instrument_quotes_generated_data, aVar2)
        if (f2_tmp != None):
            self.get_digital_spot_profit_after_sale_data[position_id]['f2'] = f2_tmp
            f2 = f2_tmp
        else:
            f2 = self.get_digital_spot_profit_after_sale_data[position_id]['f2']
        if ((spotLowerInstrumentStrike != instrumentStrikeValue) and (f != None) and (f2 != None)):
            if ((spotLowerInstrumentStrike > instrumentStrikeValue) or (instrumentStrikeValue > spotUpperInstrumentStrike)):
                if z:
                    instrumentStrikeValue = ((spotUpperInstrumentStrike - instrumentStrikeValue) / abs((spotUpperInstrumentStrike - spotLowerInstrumentStrike)))
                    f = abs((f2 - f))
                else:
                    instrumentStrikeValue = ((instrumentStrikeValue - spotUpperInstrumentStrike) / abs((spotUpperInstrumentStrike - spotLowerInstrumentStrike)))
                    f = abs((f2 - f))
            elif z:
                f += (((instrumentStrikeValue - spotLowerInstrumentStrike) / (spotUpperInstrumentStrike - spotLowerInstrumentStrike)) * (f2 - f))
            else:
                instrumentStrikeValue = ((spotUpperInstrumentStrike - instrumentStrikeValue) / (spotUpperInstrumentStrike - spotLowerInstrumentStrike))
                f -= f2
            f = (f2 + (instrumentStrikeValue * f))
        if z2:
            pass
        if (f != None):
            price = (f / getRate)
            return ((price * getAbsCount) - amount)
        else:
            return None
