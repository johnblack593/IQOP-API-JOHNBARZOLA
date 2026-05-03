"""
iqoptionapi/cli/main.py
────────────────────────
Entry point principal para la CLI con soporte para subcomandos.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from iqoptionapi.cli.config_loader import load_config, LoggingConfig, BotConfig

if TYPE_CHECKING:
    from iqoptionapi.backtest.engine import BacktestRun
    from iqoptionapi.strategy.base import BaseStrategy


logger = logging.getLogger(__name__)


def _setup_logging(log_config: LoggingConfig) -> None:
    """Configura el sistema de logging global."""
    level = getattr(logging, log_config.level, logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    
    if log_config.file:
        handlers.append(logging.FileHandler(log_config.file))
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def _launch_bot(config: BotConfig, state_file: str = "bot_state.json") -> None:
    """
    Construye IQ_Option, conecta, crea BotOrchestrator y lo lanza.
    Maneja el archivo de estado para monitoreo externo.
    """
    from iqoptionapi.stable_api import IQ_Option
    from iqoptionapi.bot.orchestrator import BotOrchestrator
    from iqoptionapi.strategy.signal_consensus import SignalConsensus
    from iqoptionapi.circuit_breaker import CircuitBreaker
    from iqoptionapi.trade_journal import TradeJournal

    # 1. Conexión
    iq = IQ_Option(
        config.iqoption.email,
        config.iqoption.password
    )
    
    check, reason = iq.connect()
    if not check:
        print(f"[ERROR] Connection failed: {reason}", file=sys.stderr)
        sys.exit(1)
    
    iq.change_balance(config.iqoption.account_type)
    
    # 2. Infraestructura
    cb = None
    if config.circuit_breaker.enabled:
        cb = CircuitBreaker(
            max_consecutive_losses=config.circuit_breaker.max_consecutive_losses,
            max_session_loss_usd=0.0,
            max_drawdown_pct=config.circuit_breaker.max_daily_loss_pct / 100.0
        )
    
    journal = TradeJournal()
    
    # 3. Consenso (vacio por ahora)
    consensus = SignalConsensus(strategies=[])
    
    # 4. Orquestador
    orchestrator = BotOrchestrator(
        iq=iq,
        consensus=consensus,
        asset=config.bot.asset,
        timeframe=config.bot.timeframe,
        trade_amount=config.bot.trade_amount,
        candles_window=config.bot.candles_window,
        dry_run=config.bot.dry_run,
        circuit_breaker=cb,
        journal=journal
    )
    
    orchestrator.start()
    
    # 5. Escribir estado inicial
    state = {
        "pid": os.getpid(),
        "started_at": datetime.now().isoformat(),
        "asset": config.bot.asset,
        "timeframe": config.bot.timeframe,
        "dry_run": config.bot.dry_run,
        "trade_count": 0,
        "last_tick": None
    }
    try:
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning("Could not write state file: %s", e)

    logger.info("Bot started. Press Ctrl+C to stop.")
    
    try:
        while orchestrator.is_running():
            # Actualizar estado periódicamente
            bot_status = orchestrator.status()
            state["trade_count"] = bot_status["trade_count"]
            state["last_tick"] = datetime.now().isoformat()
            try:
                with open(state_file, "w") as f:
                    json.dump(state, f, indent=2)
            except Exception:
                pass
            
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    finally:
        orchestrator.stop()
        if os.path.exists(state_file):
            try:
                os.remove(state_file)
            except Exception:
                pass
        logger.info("Bot stopped cleanly.")


def _make_dummy_strategy(config: BotConfig) -> BaseStrategy:
    """
    Crea una DummyStrategy que siempre retorna HOLD.
    Usada para backtest offline sin estrategias reales.
    """
    from iqoptionapi.strategy.base import BaseStrategy
    from iqoptionapi.strategy.signal import Signal, Direction, AssetType

    class _DummyStrategy(BaseStrategy):
        @property
        def name(self) -> str:
            return "DummyHold"
            
        def analyze(self, candles):
            return Signal(
                asset=config.bot.asset,
                direction=Direction.HOLD,
                duration=config.bot.timeframe,
                amount=config.bot.trade_amount,
                asset_type=AssetType.FOREX,
                confidence=0.0,
                strategy_id="dummy",
            )
            
    return _DummyStrategy(
        asset=config.bot.asset,
        asset_type=AssetType.FOREX,
        duration=config.bot.timeframe,
        amount=config.bot.trade_amount,
    )


def _print_backtest_report(result: BacktestRun, asset: str) -> None:
    """Imprime un reporte visual del backtest."""
    print("╔══════════════════════════════════════╗")
    print(f"║  BACKTEST REPORT — {result.strategy_name.ljust(18)}║")
    print("╠══════════════════════════════════════╣")
    print(f"║  Asset:          {asset.ljust(20)}║")
    print(f"║  Candles:        {str(result.total_candles).ljust(20)}║")
    print(f"║  Trades:         {str(result.total_trades).ljust(20)}║")
    print(f"║  Win Rate:       {f'{result.win_rate * 100:.1f}%'.ljust(20)}║")
    print(f"║  Profit Factor:  {f'{result.profit_factor:.2f}'.ljust(20)}║")
    print(f"║  Sharpe Ratio:   {f'{result.sharpe_ratio:.2f}'.ljust(20)}║")
    print(f"║  Max Drawdown:   {f'{result.max_drawdown_pct:.2f}%'.ljust(20)}║")
    print(f"║  Expectancy:     ${f'{result.expectancy:.2f}'.ljust(19)}║")
    print(f"║  Final Balance:  ${f'{result.final_balance:.2f}'.ljust(19)}║")
    print("╚══════════════════════════════════════╝")


def _write_backtest_json(result: BacktestRun, asset: str, path: str) -> None:
    """Escribe los resultados del backtest a un archivo JSON."""
    data = {
        "strategy_name": result.strategy_name,
        "asset": asset,
        "candles_total": result.total_candles,
        "total_trades": result.total_trades,
        "win_rate": float(result.win_rate),
        "profit_factor": float(result.profit_factor),
        "sharpe_ratio": float(result.sharpe_ratio),
        "max_drawdown_pct": float(result.max_drawdown_pct),
        "expectancy": float(result.expectancy),
        "initial_balance": float(result.initial_balance),
        "final_balance": float(result.final_balance)
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _cmd_run(args) -> None:
    """Lanza el bot en tiempo real."""
    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        config.bot.dry_run = True

    _setup_logging(config.logging)
    _launch_bot(config)


def _cmd_backtest(args) -> None:
    """Ejecuta un backtest offline."""
    if not Path(args.data).exists():
        print(f"[ERROR] Data file not found: {args.data}", file=sys.stderr)
        sys.exit(1)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    import numpy as np
    try:
        candles = np.loadtxt(
            args.data, delimiter=",",
            skiprows=1,
            dtype=float
        )
        if candles.ndim == 1:
            candles = candles.reshape(1, -1)
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}", file=sys.stderr)
        sys.exit(1)

    from iqoptionapi.backtest.engine import BacktestEngine
    
    try:
        engine = BacktestEngine(
            strategy=_make_dummy_strategy(config),
            candles=candles,
            initial_balance=config.bot.trade_amount * 100,
            trade_amount=config.bot.trade_amount,
        )
        result = engine.run()
    except ValueError as e:
        print(f"[ERROR] Backtest failed: {e}", file=sys.stderr)
        sys.exit(1)

    _print_backtest_report(result, config.bot.asset)

    if args.output:
        _write_backtest_json(result, config.bot.asset, args.output)


def _cmd_status(args) -> None:
    """Muestra el estado del bot desde el archivo de estado."""
    if not os.path.exists(args.state_file):
        print("Bot is not running.")
        return

    try:
        with open(args.state_file, "r") as f:
            state = json.load(f)
        
        print("Bot Status ─────────────────────────")
        print(f"PID:          {state.get('pid')}")
        print(f"Started:      {state.get('started_at')}")
        print(f"Asset:        {state.get('asset')} @ {state.get('timeframe')}s")
        print(f"Mode:         {'DRY RUN' if state.get('dry_run') else 'LIVE'}")
        print(f"Trades:       {state.get('trade_count')}")
        print(f"Last Tick:    {state.get('last_tick')}")
        print("─────────────────────────────────────")
    except Exception as e:
        print(f"[ERROR] Could not read status: {e}", file=sys.stderr)


def _cmd_version() -> None:
    """Imprime información de versión."""
    print("JCBV-NEXUS v9.3 — IQ Option Trading Bot")
    print(f"Python {sys.version.split()[0]} | Platform: {sys.platform}")


def main() -> None:
    """Función principal de la CLI con subparsers."""
    parser = argparse.ArgumentParser(
        prog="iqopt",
        description="JCBV-NEXUS IQ Option Trading Bot",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Subcomando: run
    run_parser = subparsers.add_parser("run", help="Launch the bot")
    run_parser.add_argument("--config", "-c", default="config.yaml", help="YAML config file")
    run_parser.add_argument("--dry-run", action="store_true", help="Override dry_run mode")

    # Subcomando: backtest
    bt_parser = subparsers.add_parser("backtest", help="Run backtest on historical CSV")
    bt_parser.add_argument("--config", "-c", default="config.yaml", help="YAML config file")
    bt_parser.add_argument("--data", "-d", required=True, help="Path to CSV candles data")
    bt_parser.add_argument("--output", "-o", default=None, help="Optional JSON output path")

    # Subcomando: status
    st_parser = subparsers.add_parser("status", help="Show bot running status")
    st_parser.add_argument("--state-file", default="bot_state.json", help="Path to state file")

    # Subcomando: version
    subparsers.add_parser("version", help="Print version")

    # Compatibilidad con flags globales
    parser.add_argument("--version", "-v", action="store_true", help="Print version and exit")

    args = parser.parse_args()

    if args.version:
        _cmd_version()
        return

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "backtest":
        _cmd_backtest(args)
    elif args.command == "status":
        _cmd_status(args)
    elif args.command == "version":
        _cmd_version()


if __name__ == "__main__":
    main()
