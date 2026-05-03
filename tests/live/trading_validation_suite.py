"""
tests/live/trading_validation_suite.py
──────────────────────────────────────
Script principal para la validación de trading real en PRACTICE.
"""

import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Forzar encoding UTF-8 en stdout si es posible en Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.core.logger import get_logger
from iqoptionapi.strategy.server_indicator_bridge import ServerIndicatorBridge

from helpers.asset_resolver import AssetResolver
from helpers.trade_executor import TradeExecutor, TradeResult
from helpers.report_builder import ReportBuilder

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%H:%M:%S')
logger = get_logger("TradingValidation")

class TradingValidationSuite:
    def __init__(self):
        self.results = []
        self.api = None
        self.initial_balance = 0.0
        self.final_balance = 0.0
        self.start_time = datetime.now()
        
        self.email = os.getenv("IQOP_EMAIL") or os.getenv("IQ_EMAIL")
        self.password = os.getenv("IQOP_PASSWORD") or os.getenv("IQ_PASSWORD")
        
        if not self.email or not self.password:
            print("[ERROR] Credenciales no encontradas (IQOP_EMAIL/IQ_EMAIL).")
            exit(1)

    def run(self):
        print(f"🚀 INICIANDO SUITE DE VALIDACIÓN DE TRADING — v9.3.721")
        print(f"📅 FECHA: {self.start_time.isoformat()}")
        print("-" * 60)

        # 1. Conexión con reintento de rotación de IP
        max_retries = 2
        for attempt in range(max_retries + 1):
            print(f"⏳ Conectando (Intento {attempt + 1}/{max_retries + 1})...")
            self.api = IQ_Option(self.email, self.password, active_account_type="PRACTICE")
            check, reason = self.api.connect()
            
            if check:
                break
                
            if "timed out" in reason.lower() and attempt < max_retries:
                print("⚠️ Timeout detectado. Posible bloqueo de IP. Rotando vía WARP...")
                from helpers.ip_rotator import rotate_ip
                if rotate_ip():
                    time.sleep(5)
                    continue
            
            print(f"❌ Error de conexión: {reason}")
            if attempt == max_retries:
                return

        # 2. Verificar Balance
        self.api.change_balance("PRACTICE")
        time.sleep(2)
        self.initial_balance = self.api.get_balance()
        print(f"💰 Balance Inicial (PRACTICE): ${self.initial_balance:.2f}")
        
        if self.initial_balance < 500:
            print("⚠️ Balance bajo (< $500). Se usarán montos mínimos absolutos.")

        # 3. Inicializar Helpers
        self.resolver = AssetResolver(self.api)
        self.resolver.sync()
        self.executor = TradeExecutor(self.api)
        self.report = ReportBuilder(self.results, self._get_metadata())

        # 4. GRUPO A: OPCIONES
        self.run_group_a()
        self.report.build("tests/live/TRADING_VALIDATION_REPORT_A.md")

        # 5. GRUPO B: MARGEN
        self.run_group_b()
        self.report.build("tests/live/TRADING_VALIDATION_REPORT_B.md")

        # 6. Finalización
        self.final_balance = self.api.get_balance()
        print("-" * 60)
        print(f"✅ Validación Completada. Generando reporte final...")
        
        self.report.metadata.update({"final_balance": self.final_balance})
        self.report.build("tests/live/TRADING_VALIDATION_REPORT.md")
        
        print(f"📄 Reporte generado: tests/live/TRADING_VALIDATION_REPORT.md")
        print(f"💰 Balance Final: ${self.final_balance:.2f} (PnL: ${self.final_balance - self.initial_balance:+.2f})")

    def _get_metadata(self):
        return {
            "start_time": self.start_time,
            "initial_balance": self.initial_balance,
            "final_balance": self.final_balance,
            "sdk_version": "9.3.721"
        }
        
        builder = ReportBuilder(self.results, metadata)
        builder.build("tests/live/TRADING_VALIDATION_REPORT.md")
        
        print(f"📄 Reporte generado: tests/live/TRADING_VALIDATION_REPORT.md")
        print(f"💰 Balance Final: ${self.final_balance:.2f} (PnL: ${self.final_balance - self.initial_balance:+.2f})")

    def run_group_a(self):
        print("\n[GRUPO A] Iniciando Opciones (Binary, Turbo, Digital, Blitz)...")
        subcategories = ["blitz", "binary", "digital"]
        
        for sub in subcategories:
            asset = self.resolver.resolve(sub)
            if not asset:
                print(f"  ⚠️ {sub}: No hay activos disponibles. Saltando.")
                continue
            
            print(f"  📍 {sub.upper()}: Usando {asset}")
            
            # Asegurar que tenemos precios en tiempo real para este activo
            self.api.subscribe_short_active_info(asset)
            time.sleep(1) # Esperar a que llegue el primer quote
            
            # A.X.1 Obtener dirección sugerida
            indicator_raw = self.api.get_technical_indicators(asset)
            direction = "CALL"
            consensus_msg = "NEUTRAL (Default to CALL)"
            
            if indicator_raw:
                bridge = ServerIndicatorBridge(indicator_raw)
                if not bridge.is_empty():
                    consensus = bridge.consensus_direction()
                    direction = "CALL" if "BUY" in consensus.name else "PUT" if "SELL" in consensus.name else "CALL"
                    consensus_msg = consensus.name

            amount = self.resolver.get_min_amount(asset, sub)
            
            # A.X.4 Ejecución (CALL/PUT)
            for d in [direction, "PUT" if direction == "CALL" else "CALL"]:
                print(f"    - Ejecutando {d} (${amount}) y esperando resultado...")
                
                if sub == "blitz":
                    # blitz usa buy_blitz pero TradeExecutor lo mapea a place_binary_option con subcategory="blitz"
                    res = self.executor.place_binary_option(asset, d, amount, 60, subcategory="blitz")
                elif sub == "binary":
                    res = self.executor.place_binary_option(asset, d, amount, 60)
                elif sub == "digital":
                    res = self.executor.place_digital_option(asset, d, amount, 60)
                
                res.server_indicators = {"consensus": consensus_msg}
                self.results.append(res)
                print(f"      Result: {res.result} (PnL: {res.profit_usd:+.2f})")
                time.sleep(1 + __import__('random').random()) # Jitter para stealth

    def run_group_b(self):
        print("\n[GRUPO B] Iniciando Margen (Forex, Stocks, Crypto, Commodity, Index, ETF)...")
        subcategories = ["forex", "stocks", "crypto", "commodity", "index", "etf"]
        
        for sub in subcategories:
            asset = self.resolver.resolve(sub)
            if not asset:
                print(f"  ⚠️ {sub}: No hay activos disponibles. Saltando.")
                continue
            
            print(f"  📍 {sub.upper()}: Usando {asset}")
            
            amount = self.resolver.get_min_amount(asset, sub)
            # Leverage por defecto conservador
            leverage = 1
            
            # Mapear instrument_type interno de IQ Option
            itype_map = {
                "forex": "forex",
                "stocks": "stock",
                "crypto": "crypto",
                "commodity": "commodity",
                "index": "index",
                "etf": "etf"
            }
            itype = itype_map[sub]
            
            for d in ["buy", "sell"]:
                print(f"    - Ejecutando {d.upper()} (${amount}) leverage={leverage}...")
                res = self.executor.place_margin_order(itype, asset, d, amount, leverage, subcategory=sub)
                res.metadata = {"leverage": leverage}
                self.results.append(res)
                print(f"      Result: {res.result} (PnL: {res.profit_usd:+.2f})")
                time.sleep(1 + __import__('random').random()) # Jitter para stealth

if __name__ == "__main__":
    suite = TradingValidationSuite()
    suite.run()
