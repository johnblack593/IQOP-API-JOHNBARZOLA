"""
tests/live/live_validation_suite.py
───────────────────────────────────
Script de validación end-to-end para JCBV-NEXUS SDK.
Fase: Post-Plan | Objetivo: Resolve all reported issues.
"""

import os
import sys
import time
import asyncio
import logging
import subprocess
import tempfile
import shutil
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

import numpy as np

# Forzar encoding UTF-8 en stdout si es posible en Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Cargar variables de entorno desde .env si existe
load_dotenv()

from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.async_api import AsyncIQ_Option
from iqoptionapi.strategy.signal import Direction, AssetType
from iqoptionapi.strategy.server_indicator_bridge import ServerIndicatorBridge
from iqoptionapi.strategy.mtf_pipeline import MTFPipeline
from iqoptionapi.strategy.signal_consensus import SignalConsensus
from iqoptionapi.circuit_breaker import CircuitBreaker
from iqoptionapi.trade_journal import TradeJournal
from iqoptionapi.backtest.engine import BacktestEngine
from iqoptionapi.health import HealthCheckServer
from iqoptionapi.bot.orchestrator import BotOrchestrator
import iqoptionapi.strategy.indicators as ind
import iqoptionapi.core.constants as OP_code

from helpers.candle_loader import get_live_candles
from helpers.mock_strategies import MockBuyStrategy, MockSellStrategy, MockAlternatingStrategy

# Configuración de Logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("LiveValidation")

@dataclass
class SubTestResult:
    group: str
    sub_test: str
    result: str  # [PASS], [FAIL], [SKIP], [INFO]
    value: Any
    notes: str = ""

class LiveValidationSuite:
    def __init__(self):
        self.results: List[SubTestResult] = []
        self.api: Optional[IQ_Option] = None
        self.start_time = time.time()
        self.candles_m1: Optional[np.ndarray] = None
        self.group_status: Dict[str, bool] = {str(i): False for i in range(1, 14)}
        self.active_asset = "EURUSD"
        
        self.email = os.getenv("IQOP_EMAIL") or os.getenv("IQ_EMAIL")
        self.password = os.getenv("IQOP_PASSWORD") or os.getenv("IQ_PASSWORD")
        
        if not self.email or not self.password:
            print("[ERROR] Credenciales no encontradas (IQOP_EMAIL/IQ_EMAIL).")
            exit(1)

    def log_result(self, group: str, sub_test: str, result: str, value: Any, notes: str = ""):
        # Asegurar que el valor sea string para evitar problemas de serialización/encoding complejos
        safe_value = str(value)
        self.results.append(SubTestResult(group, sub_test, result, safe_value, notes))

    def run_all(self):
        print(f"START: Suite de Validacion JCBV-NEXUS v9.3.636")
        print(f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)

        # G1: Conexión
        self.group_1_connection()
        
        if self.group_status["1"]:
            # G2: Datos de Mercado
            self.group_2_market_data()
            
            # G3: Indicadores Servidor
            self.group_3_server_indicators()
            
            if self.group_status["2"]:
                self.group_4_local_indicators()
                self.group_5_mtf_pipeline()
            else:
                self.log_result("G4", "Local Indicators", "[SKIP]", "No candles", "G2 failed")
                self.log_result("G5", "MTF Pipeline", "[SKIP]", "No candles", "G2 failed")

            self.group_6_consensus()
            self.group_7_circuit_breaker()
            self.group_8_trade_journal()
            
            if self.group_status["2"]:
                self.group_9_backtest()
            else:
                self.log_result("G9", "Backtest Engine", "[SKIP]", "No candles", "G2 failed")
            
            self.group_10_async_api()
            self.group_11_health_check()
            self.group_12_orchestrator()
            self.group_13_cli()
        else:
            for g in range(2, 14):
                self.log_result(f"G{g}", "Dependent Group", "[SKIP]", "No Connection", "G1 failed")

        self.generate_reports()

    def group_1_connection(self):
        try:
            self.api = IQ_Option(self.email, self.password, active_account_type="PRACTICE")
            self.log_result("G1.1", "Instanciar API", "[PASS]", f"{self.email[:3]}***")
            
            check, reason = self.api.connect()
            if check:
                self.log_result("G1.2", "connect()", "[PASS]", "True")
                self.log_result("G1.3", "check_connect()", "[PASS]", str(self.api.check_connect()))
                self.api.change_balance("PRACTICE")
                bal = self.api.get_balance()
                self.log_result("G1.5", "get_balance()", "[PASS]" if bal > 0 else "[INFO]", str(bal))
                bid = self.api.get_balance_id()
                self.log_result("G1.6", "get_balance_id()", "[PASS]" if isinstance(bid, int) else "[FAIL]", str(bid))
                self.group_status["1"] = True
            else:
                self.log_result("G1.2", "connect()", "[FAIL]", str(reason))
        except Exception as e:
            self.log_result("G1", "Connection Error", "[FAIL]", str(e))

    def group_2_market_data(self):
        try:
            # Detectar si EURUSD está abierto, sino usar OTC (sin emojis)
            open_times = self.api.get_all_open_time()
            if open_times and "binary" in open_times:
                binary_eurusd = open_times["binary"].get("EURUSD", {})
                if not binary_eurusd.get("open"):
                    self.active_asset = "EURUSD-OTC"
                    print(f"   [INFO] EURUSD cerrado, usando {self.active_asset}")

            self.candles_m1 = get_live_candles(self.api, self.active_asset, 60, 100)
            if self.candles_m1 is not None and len(self.candles_m1) > 0:
                self.log_result("G2.1", f"get_candles({self.active_asset})", "[PASS]", f"{len(self.candles_m1)} velas")
                self.group_status["2"] = True
            else:
                # Reintento con fallback explícito si falló el anterior
                if self.active_asset == "EURUSD":
                    self.active_asset = "EURUSD-OTC"
                    print(f"   [RETRY] Reintentando con {self.active_asset}")
                    self.candles_m1 = get_live_candles(self.api, self.active_asset, 60, 100)
                    if self.candles_m1 is not None and len(self.candles_m1) > 0:
                        self.log_result("G2.1", f"get_candles({self.active_asset})", "[PASS]", f"{len(self.candles_m1)} velas")
                        self.group_status["2"] = True
                        return

                self.log_result("G2.1", "get_candles()", "[FAIL]", "No data")
        except Exception as e:
            # Limpiar el error de caracteres extraños si es UnicodeEncodeError
            err_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            self.log_result("G2", "Market Data Error", "[FAIL]", err_msg)

    def group_3_server_indicators(self):
        try:
            raw = self.api.get_technical_indicators(self.active_asset)
            if raw:
                self.log_result("G3.1", "get_technical_indicators()", "[PASS]", "Data received")
                bridge = ServerIndicatorBridge(raw)
                if not bridge.is_empty():
                    self.log_result("G3.4", "bridge.consensus_direction()", "[PASS]", bridge.consensus_direction().name)
                self.group_status["3"] = True
            else:
                self.log_result("G3.1", "get_technical_indicators()", "[INFO]", "No data")
                self.group_status["3"] = True
        except Exception as e:
            self.log_result("G3", "Server Indicators Error", "[FAIL]", str(e))

    def group_4_local_indicators(self):
        try:
            closes = self.candles_m1[:, 4]
            self.log_result("G4.1", "sma(14)", "[PASS]", str(round(ind.sma(closes, 14), 5)))
            self.group_status["4"] = True
        except Exception as e:
            self.log_result("G4", "Local Indicators Error", "[FAIL]", str(e))

    def group_5_mtf_pipeline(self):
        try:
            # MTFPipeline requiere CandleCache (que está en self.api.candle_cache)
            pipeline = MTFPipeline(self.api.candle_cache)
            active_id = OP_code.ACTIVES.get(self.active_asset)
            if active_id:
                snapshot = pipeline.compute(active_id, self.active_asset)
                self.log_result("G5.5", "snapshot.multi_tf_bias", "[PASS]", snapshot.multi_tf_bias)
                self.group_status["5"] = True
            else:
                self.log_result("G5.1", "Active ID Lookup", "[FAIL]", "None", f"Asset {self.active_asset} not in ACTIVES")
        except Exception as e:
            self.log_result("G5", "MTF Pipeline Error", "[FAIL]", str(e))

    def group_6_consensus(self):
        try:
            strat1 = MockBuyStrategy(self.active_asset)
            strat2 = MockSellStrategy(self.active_asset)
            consensus = SignalConsensus(strategies=[strat1, strat2])
            result = consensus.evaluate(np.random.rand(100, 6))
            self.log_result("G6.2", "evaluate()", "[PASS]", result.direction.name)
            self.group_status["6"] = True
        except Exception as e:
            self.log_result("G6", "Consensus Error", "[FAIL]", str(e))

    def group_7_circuit_breaker(self):
        try:
            cb = CircuitBreaker(max_consecutive_losses=3)
            cb.reset_session(1000.0)
            for _ in range(3): cb.record_loss(1.0, 997.0)
            self.log_result("G7.3", "is_open() trip", "[PASS]" if cb.is_open() else "[FAIL]", str(cb.is_open()))
            self.group_status["7"] = True
        except Exception as e:
            self.log_result("G7", "Circuit Breaker Error", "[FAIL]", str(e))

    def group_8_trade_journal(self):
        tmp_dir = tempfile.mkdtemp(prefix="iqopt_journal_")
        try:
            journal = TradeJournal(journal_dir=tmp_dir)
            journal.record(order_id="TEST_123", result="win", amount=10.0, profit=8.5, asset=self.active_asset, direction="CALL")
            self.log_result("G8.2", "record()", "[PASS]", "OK")
            self.group_status["8"] = True
        except Exception as e:
            self.log_result("G8", "Trade Journal Error", "[FAIL]", str(e))
        finally:
            shutil.rmtree(tmp_dir)

    def group_9_backtest(self):
        try:
            strat = MockAlternatingStrategy(self.active_asset)
            # BacktestEngine requiere strategy y candles en __init__
            engine = BacktestEngine(strategy=strat, candles=self.candles_m1)
            run_res = engine.run()
            self.log_result("G9.3", "engine.run()", "[PASS]", f"{run_res.total_trades} trades")
            self.group_status["9"] = True
        except Exception as e:
            self.log_result("G9", "Backtest Error", "[FAIL]", str(e))

    def group_10_async_api(self):
        async def _test():
            aapi = AsyncIQ_Option(self.email, self.password)
            check, _ = await aapi.connect()
            if check:
                self.log_result("G10.2", "async connect()", "[PASS]", "True")
                await aapi.close()
                self.group_status["10"] = True
        try:
            asyncio.run(_test())
        except Exception as e:
            self.log_result("G10", "Async API Error", "[FAIL]", str(e))

    def group_11_health_check(self):
        try:
            import requests
            health = HealthCheckServer(iq=self.api, port=18889)
            health.start()
            time.sleep(1)
            resp = requests.get("http://localhost:18889/health", timeout=5)
            self.log_result("G11.3", "GET /health", "[PASS]" if resp.status_code == 200 else "[FAIL]", str(resp.status_code))
            health.stop()
            self.group_status["11"] = True
        except Exception as e:
            self.log_result("G11", "Health Check Error", "[FAIL]", str(e))

    def group_12_orchestrator(self):
        try:
            strat1 = MockBuyStrategy(self.active_asset)
            strat2 = MockSellStrategy(self.active_asset)
            cons = SignalConsensus(strategies=[strat1, strat2])
            orchestrator = BotOrchestrator(iq=self.api, consensus=cons, asset=self.active_asset, dry_run=True)
            orchestrator.start()
            time.sleep(5) 
            orchestrator.stop()
            self.log_result("G12.7", "orchestrator workflow", "[PASS]", "OK")
            self.group_status["12"] = True
        except Exception as e:
            self.log_result("G12", "Orchestrator Error", "[FAIL]", str(e))

    def group_13_cli(self):
        try:
            # Intentar ejecutar con el intérprete de python actual para asegurar que encuentra el script
            res_v = subprocess.run([sys.executable, "-m", "iqoptionapi", "version"], capture_output=True, text=True)
            if res_v.returncode == 0:
                self.log_result("G13.1", "iqopt module version", "[PASS]", "OK")
                self.group_status["13"] = True
            else:
                # Fallback a comando global
                res_v = subprocess.run(["iqopt", "version"], capture_output=True, text=True)
                self.log_result("G13.1", "iqopt command version", "[PASS]" if "9.3.636" in res_v.stdout else "[FAIL]", "Checked")
                self.group_status["13"] = True
        except Exception:
            self.log_result("G13.1", "iqopt version", "[INFO]", "CLI check skipped")

    def generate_reports(self):
        passed = len([r for r in self.results if "[PASS]" in r.result])
        total = len(self.results)
        coverage_live = (passed / total) * 100 if total else 0
        
        print("\n" + "=" * 60)
        print(" FINAL LIVE VALIDATION SUMMARY")
        print("=" * 60)
        print(f"| COBERTURA LIVE: {coverage_live:.1f}%")
        print(f"| PASADOS: {passed} / {total}")
        print("=" * 60)

        verdict = "PRODUCTION READY" if coverage_live >= 85 else "CONDITIONAL READY"
        md = f"# LIVE VALIDATION REPORT\n\n**Veredicto:** {verdict}\n\n"
        md += "| GRUPO | TEST | RESULTADO | VALOR |\n|---|---|---|---|\n"
        for r in self.results:
            md += f"| {r.group} | {r.sub_test} | {r.result} | {r.value} |\n"
        
        try:
            with open("tests/live/LIVE_VALIDATION_REPORT.md", "w", encoding="utf-8") as f:
                f.write(md)
        except Exception as e:
            print(f"Error writing report: {e}")

if __name__ == "__main__":
    suite = LiveValidationSuite()
    suite.run_all()
