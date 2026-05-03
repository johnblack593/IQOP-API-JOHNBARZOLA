"""
iqoptionapi/cli/config_loader.py
────────────────────────────────
Cargador y validador de configuración YAML.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required for YAML config support. Install with: pip install PyYAML")


@dataclass
class IQOptionConfig:
    email:        str
    password:     str
    account_type: str = "PRACTICE"


@dataclass
class BotSettings:
    asset:          str   = "EURUSD"
    timeframe:      int   = 60
    trade_amount:   float = 1.0
    candles_window: int   = 100
    dry_run:        bool  = True


@dataclass
class CircuitBreakerConfig:
    enabled:                bool  = True
    max_daily_loss_pct:     float = 10.0
    max_consecutive_losses: int   = 5


@dataclass
class LoggingConfig:
    level: str        = "INFO"
    file:  Optional[str] = None


@dataclass
class BotConfig:
    iqoption:        IQOptionConfig
    bot:             BotSettings = field(default_factory=BotSettings)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    logging:         LoggingConfig = field(default_factory=LoggingConfig)
    strategies:      list[dict] = field(default_factory=list)


def load_config(path: str) -> BotConfig:
    """
    Carga y valida el archivo YAML en `path`.
    Retorna BotConfig o lanza ValueError con mensaje descriptivo.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            raw = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Error parsing YAML: {e}")

    if not raw:
        raise ValueError("Empty config file")

    if "iqoption" not in raw:
        raise ValueError("Missing required section: iqoption")

    # 1. IQ Option Config
    iq_raw = raw.get("iqoption", {})
    if "email" not in iq_raw:
        raise ValueError("Missing required field: iqoption.email")
    if "password" not in iq_raw:
        raise ValueError("Missing required field: iqoption.password")
    
    account_type = iq_raw.get("account_type", "PRACTICE").upper()
    if account_type not in ["PRACTICE", "REAL"]:
        raise ValueError(f"Invalid account_type: {account_type}. Must be PRACTICE or REAL")

    iq_config = IQOptionConfig(
        email=iq_raw["email"],
        password=iq_raw["password"],
        account_type=account_type
    )

    # 2. Bot Settings
    bot_raw = raw.get("bot", {})
    timeframe = bot_raw.get("timeframe", 60)
    valid_timeframes = [1, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600]
    if timeframe not in valid_timeframes:
        raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {valid_timeframes}")

    trade_amount = float(bot_raw.get("trade_amount", 1.0))
    if trade_amount < 1.0:
        raise ValueError(f"Invalid trade_amount: {trade_amount}. Minimum is 1.0")

    bot_settings = BotSettings(
        asset=bot_raw.get("asset", "EURUSD"),
        timeframe=timeframe,
        trade_amount=trade_amount,
        candles_window=bot_raw.get("candles_window", 100),
        dry_run=bot_raw.get("dry_run", True)
    )

    # 3. Circuit Breaker
    cb_raw = raw.get("circuit_breaker", {})
    cb_config = CircuitBreakerConfig(
        enabled=cb_raw.get("enabled", True),
        max_daily_loss_pct=float(cb_raw.get("max_daily_loss_pct", 10.0)),
        max_consecutive_losses=int(cb_raw.get("max_consecutive_losses", 5))
    )

    # 4. Logging
    log_raw = raw.get("logging", {})
    log_level = log_raw.get("level", "INFO").upper()
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        raise ValueError(f"Invalid logging level: {log_level}")

    log_config = LoggingConfig(
        level=log_level,
        file=log_raw.get("file")
    )

    # 5. Strategies
    strategies = raw.get("strategies", [])

    return BotConfig(
        iqoption=iq_config,
        bot=bot_settings,
        circuit_breaker=cb_config,
        logging=log_config,
        strategies=strategies
    )
