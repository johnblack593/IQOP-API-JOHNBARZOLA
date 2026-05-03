"""
iqoptionapi/cli/main.py
────────────────────────
Entry point principal para la CLI.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time

from iqoptionapi.cli.config_loader import load_config, LoggingConfig, BotConfig


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


def _launch_bot(config: BotConfig) -> None:
    """
    Construye IQ_Option, conecta, crea BotOrchestrator y lo lanza.
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
            max_session_loss_usd=0.0, # S9-T2 implementará esto mejor
            max_drawdown_pct=config.circuit_breaker.max_daily_loss_pct / 100.0
        )
    
    journal = TradeJournal()
    
    # 3. Consenso (vacio por ahora en T1)
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
    logger.info("Bot started. Press Ctrl+C to stop.")
    
    try:
        while orchestrator.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    finally:
        orchestrator.stop()
        logger.info("Bot stopped cleanly.")


def main() -> None:
    """Función principal de la CLI."""
    parser = argparse.ArgumentParser(
        prog="iqopt",
        description="JCBV-NEXUS IQ Option Trading Bot v9.3",
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to YAML config file (default: config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Override dry_run from config (forces simulation mode)",
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Print version and exit",
    )
    
    args = parser.parse_args()
    
    if args.version:
        print("JCBV-NEXUS v9.3 — IQ Option Trading Bot")
        return

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    # Override dry_run si se pasó por CLI
    if args.dry_run:
        config.bot.dry_run = True

    # Configurar logging
    _setup_logging(config.logging)

    # Lanzar
    _launch_bot(config)


if __name__ == "__main__":
    main()
