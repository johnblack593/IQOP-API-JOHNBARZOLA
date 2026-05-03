"""
tests/live/helpers/trade_executor.py
────────────────────────────────────
Ejecuta trades reales en PRACTICE y espera resultados detallados.
"""

import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from iqoptionapi.core.logger import get_logger
import iqoptionapi.core.constants as OP_code

@dataclass
class TradeResult:
    order_id: str
    asset: str
    instrument_type: str      # binary, digital, turbo, forex, crypto...
    group: str                # "A" o "B"
    subcategory: str          # blitz, binary, digital, forex, stocks...
    direction: str            # CALL / PUT / buy / sell
    amount: float
    duration_sec: int
    open_price: float = None
    close_price: float = None
    result: str = "PENDING"   # WIN / LOSS / EQUAL / TIMEOUT / ERROR
    profit_usd: float = 0.0
    duration_ms: int = 0
    signal_confidence: float = 0.0
    server_indicators: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error_detail: str = None
    raw_response: Any = None

class TradeExecutor:
    def __init__(self, api):
        self.api = api
        self.logger = get_logger(__name__)

    def place_binary_option(self, asset: str, direction: str, amount: float, duration_sec: int, subcategory: str = "binary") -> TradeResult:
        """Ejecuta una opción binaria/turbo y espera resultado."""
        res = TradeResult(
            order_id="0", asset=asset, instrument_type="binary", 
            group="A", subcategory=subcategory, direction=direction.upper(),
            amount=amount, duration_sec=duration_sec
        )
        
        try:
            start_t = time.time()
            
            # S15-T2: Manejo especial para Blitz
            if subcategory == "blitz":
                active_id = OP_code.ACTIVES.get(asset)
                # Intentar obtener precio actual (spot)
                current_price = 0.0
                if hasattr(self.api, "current_prices") and active_id in self.api.current_prices:
                    current_price = self.api.current_prices[active_id]
                else:
                    # Fallback a candles
                    candles = self.api.get_candles(asset, 1, 1, time.time())
                    if candles: current_price = candles[0]["close"]
                
                if current_price == 0:
                    res.result = "ERROR"
                    res.error_detail = "Could not fetch current price for Blitz"
                    return res
                
                # OrdersMixin: buy_blitz(self, active, amount, action, current_price, duration=5)
                success, order_id = self.api.buy_blitz(asset, amount, direction.lower(), current_price)
            else:
                # api.buy retorna (success, order_id)
                success, order_id = self.api.buy(amount, asset, direction.lower(), duration_sec // 60)
            
            if not success:
                res.result = "ERROR"
                res.error_detail = f"SDK rejected buy ({subcategory}): {order_id}"
                return res
            
            res.order_id = str(order_id)
            
            # Esperar resultado (v3 retorna (True, win_status))
            check, win_status = self.api.check_win_v3(order_id)
            
            res.duration_ms = int((time.time() - start_t) * 1000)
            
            if check:
                res.result = win_status.upper() if isinstance(win_status, str) else str(win_status)
                # Intentar obtener profit real de betinfo
                _, info = self.api.get_betinfo(order_id)
                if info:
                    res.open_price = info.get("open_quote")
                    res.close_price = info.get("close_quote")
                    res.profit_usd = info.get("win_amount", 0.0) - amount if res.result == "WIN" else -amount
                    res.raw_response = info
            else:
                res.result = "TIMEOUT"
                
        except Exception as e:
            res.result = "ERROR"
            res.error_detail = traceback.format_exc()
            
        return res

    def place_digital_option(self, asset: str, direction: str, amount: float, duration_sec: int) -> TradeResult:
        """Ejecuta una opción digital y espera resultado."""
        res = TradeResult(
            order_id="0", asset=asset, instrument_type="digital", 
            group="A", subcategory="digital", direction=direction.upper(),
            amount=amount, duration_sec=duration_sec
        )
        
        try:
            start_t = time.time()
            # api.buy_digital_spot retorna (success, order_id)
            success, order_id = self.api.buy_digital_spot(asset, amount, direction.lower(), duration_sec // 60)
            
            if not success:
                res.result = "ERROR"
                res.error_detail = f"SDK rejected digital buy: {order_id}"
                return res
            
            res.order_id = str(order_id)
            
            # check_win_digital_v2 retorna (True, win_status)
            check, win_status = self.api.check_win_digital_v2(order_id)
            
            res.duration_ms = int((time.time() - start_t) * 1000)
            
            if check:
                res.result = win_status.upper() if isinstance(win_status, str) else str(win_status)
                # Intentar obtener info de la posición
                _, pos_info = self.api.get_digital_position(order_id)
                if pos_info:
                    res.raw_response = pos_info
                    # Digital info es más compleja, a veces está en 'msg'
            else:
                res.result = "TIMEOUT"
                
        except Exception as e:
            res.result = "ERROR"
            res.error_detail = traceback.format_exc()
            
        return res

    def place_turbo_option(self, asset: str, direction: str, amount: float, duration_sec: int = 60) -> TradeResult:
        return self.place_binary_option(asset, direction, amount, duration_sec, subcategory="turbo")

    def place_margin_order(self, instrument_type: str, asset: str, direction: str, amount: float, leverage: int, subcategory: str = None) -> TradeResult:
        """Ejecuta una orden de margen, espera a que abra y la cierra."""
        res = TradeResult(
            order_id="0", asset=asset, instrument_type=instrument_type, 
            group="B", subcategory=subcategory or instrument_type, direction=direction.lower(),
            amount=amount, duration_sec=0
        )
        
        try:
            start_t = time.time()
            # buy_order retorna (success, order_id)
            success, order_id = self.api.buy_order(
                instrument_type=instrument_type,
                instrument_id=asset,
                side=direction.lower(),
                amount=amount,
                leverage=leverage,
                type="market"
            )
            
            if not success:
                res.result = "ERROR"
                res.error_detail = f"SDK rejected margin order: {order_id}"
                return res
            
            res.order_id = str(order_id)
            
            # Esperar 5s como indica el requerimiento para que la posición se estabilice
            time.sleep(5)
            
            # Verificar orden abierta
            check, order_data = self.api.get_order(order_id)
            if not check or not order_data:
                res.result = "TIMEOUT"
                return res
            
            res.open_price = order_data.get("avg_price")
            position_id = order_data.get("position_id")
            
            # Cerrar posición
            close_check = self.api.close_position(position_id)
            if not close_check:
                res.result = "ERROR"
                res.error_detail = "Failed to close position"
                return res
            
            # Esperar un momento para que el PnL se liquide
            time.sleep(2)
            
            # En v9.3.x close_position actualiza close_position_data
            if hasattr(self.api, "close_position_data"):
                res.profit_usd = self.api.close_position_data.get("msg", {}).get("pnl_realized", 0.0)
                res.close_price = self.api.close_position_data.get("msg", {}).get("close_price")
                res.result = "WIN" if res.profit_usd > 0 else "LOSS"
                res.raw_response = self.api.close_position_data
            
            res.duration_ms = int((time.time() - start_t) * 1000)
            
        except Exception as e:
            res.result = "ERROR"
            res.error_detail = traceback.format_exc()
            
        return res
