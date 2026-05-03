"""
iqoptionapi/bot/orchestrator.py
───────────────────────────────
BotOrchestrator — el "main loop" del bot de trading.
Une la conexión al servidor, el consenso de señales y la ejecución de órdenes.

Sprint 8 · Tarea S8-T1
"""
from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Optional

import numpy as np

from iqoptionapi.strategy.signal import Direction

if TYPE_CHECKING:
    from iqoptionapi.stable_api import IQ_Option
    from iqoptionapi.strategy.signal_consensus import SignalConsensus


logger = logging.getLogger(__name__)


class BotOrchestrator:
    """
    Orquestador que ejecuta un ciclo de análisis y trading continuo.
    
    Se encarga de:
      1. Obtener velas del servidor.
      2. Evaluar señales mediante SignalConsensus.
      3. Ejecutar órdenes (reales o simuladas).
    """

    def __init__(
        self,
        iq: IQ_Option,
        consensus: SignalConsensus,
        asset: str = "EURUSD",
        timeframe: int = 60,
        trade_amount: float = 1.0,
        candles_window: int = 100,
        dry_run: bool = True,
    ) -> None:
        """
        Args:
            iq:              Instancia de IQ_Option (debe estar conectada).
            consensus:       Instancia de SignalConsensus con estrategias cargadas.
            asset:           Activo a operar (ej: "EURUSD").
            timeframe:       Segundos por vela (ej: 60 para M1).
            trade_amount:    Monto por operación.
            candles_window:  Número de velas a descargar para el análisis.
            dry_run:         Si es True, no ejecuta órdenes reales.
        """
        self.iq = iq
        self.consensus = consensus
        self.asset = asset
        self.timeframe = timeframe
        self.trade_amount = trade_amount
        self.candles_window = candles_window
        self.dry_run = dry_run

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._trade_count = 0

    def start(self) -> None:
        """Lanza el ciclo principal en un thread separado."""
        if self._running or (self._thread and self._thread.is_alive()):
            logger.warning("BotOrchestrator is already running.")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, 
            name="iqopt-orchestrator", 
            daemon=True
        )
        self._thread.start()
        logger.info("BotOrchestrator started for %s (%ds)", self.asset, self.timeframe)

    def stop(self) -> None:
        """Detiene el orquestador limpiamente."""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("Orchestrator stopped.")

    def is_running(self) -> bool:
        """Retorna True si el thread interno está activo."""
        return self._thread is not None and self._thread.is_alive()

    def status(self) -> dict:
        """Retorna el estado actual del orquestador."""
        return {
            "running": self.is_running(),
            "asset": self.asset,
            "timeframe": self.timeframe,
            "trade_count": self._trade_count,
            "dry_run": self.dry_run,
        }

    def _run_loop(self) -> None:
        """Ciclo principal de ejecución."""
        while self._running:
            try:
                self._tick()
            except Exception as e:
                logger.error("Tick error: %s", e, exc_info=True)
            
            # Esperar al siguiente tick (velas se actualizan por timeframe)
            # Nota: S8-T1 especifica esperar self.timeframe
            time.sleep(self.timeframe)
        
        self._running = False

    def _tick(self) -> None:
        """Un solo paso del ciclo de trading."""
        # 1. Obtener velas
        candles = self._fetch_candles()
        
        # 2. Validar suficientes velas (mínimo 30 para indicadores estándar)
        if candles is None or len(candles) < 30:
            logger.warning("Insufficient candles for %s: %s", 
                           self.asset, len(candles) if candles is not None else 0)
            return

        # 3. Evaluar señal
        result = self.consensus.evaluate(candles)
        
        # 4. Si no es accionable (HOLD o consenso insuficiente), salir
        if not result.is_actionable:
            return

        logger.info("Signal: %s | score=%.2f | asset=%s", 
                    result.direction, result.composite_score, self.asset)

        # 5. Ejecución (Dry Run vs Real)
        if self.dry_run:
            logger.info("[DRY RUN] Would trade %s %.2f on %s", 
                        result.direction, self.trade_amount, self.asset)
            self._trade_count += 1
            return

        # 6. Ejecutar orden real
        self._execute_order(result.direction)
        self._trade_count += 1

    def _fetch_candles(self) -> Optional[np.ndarray]:
        """Obtiene velas del servidor y las convierte a numpy (N, 6)."""
        try:
            # iq.get_candles(active, size, count, datatime)
            candles_raw = self.iq.get_candles(
                self.asset, 
                self.timeframe, 
                self.candles_window, 
                time.time()
            )
            
            if not candles_raw:
                return None

            # Formato esperado por BacktestEngine y estrategias:
            # [time (from), open, max, min, close, volume]
            rows = []
            for v in candles_raw:
                rows.append([
                    float(v["from"]),
                    float(v["open"]),
                    float(v["max"]),
                    float(v["min"]),
                    float(v["close"]),
                    float(v["volume"]),
                ])
            
            return np.array(rows, dtype=np.float64)

        except Exception as e:
            logger.warning("Failed to fetch/convert candles for %s: %s", self.asset, e)
            return None

    def _execute_order(self, direction: Direction) -> None:
        """Ejecuta una orden de compra en el servidor."""
        try:
            action = "call" if direction == Direction.CALL else "put"
            
            # iq.buy(amount, active, action, duration)
            success, order_id = self.iq.buy(
                self.trade_amount, 
                self.asset, 
                action, 
                self.timeframe
            )
            
            if success:
                logger.info("Order placed: %s | %s %.2f", order_id, action, self.trade_amount)
            else:
                logger.warning("Order failed for %s on %s: %s", action, self.asset, order_id)

        except Exception as e:
            logger.error("Order execution error on %s: %s", self.asset, e)
