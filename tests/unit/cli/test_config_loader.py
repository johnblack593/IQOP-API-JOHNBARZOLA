"""
tests/unit/cli/test_config_loader.py
────────────────────────────────────
Pruebas unitarias para el cargador de configuración YAML.
"""
from __future__ import annotations

import os
import yaml
import pytest
from iqoptionapi.cli.config_loader import load_config, BotConfig


@pytest.fixture
def minimal_yaml(tmp_path):
    """Crea un YAML mínimo válido."""
    d = tmp_path / "config.yaml"
    content = {
        "iqoption": {
            "email": "test@example.com",
            "password": "secret"
        }
    }
    d.write_text(yaml.dump(content))
    return str(d)


@pytest.fixture
def full_yaml(tmp_path):
    """Crea un YAML completo válido."""
    d = tmp_path / "full.yaml"
    content = {
        "iqoption": {
            "email": "full@example.com",
            "password": "pass",
            "account_type": "REAL"
        },
        "bot": {
            "asset": "EURUSD",
            "timeframe": 300,
            "trade_amount": 10.0,
            "candles_window": 500,
            "dry_run": False
        },
        "circuit_breaker": {
            "enabled": True,
            "max_daily_loss_pct": 5.0,
            "max_consecutive_losses": 3
        },
        "logging": {
            "level": "DEBUG",
            "file": "bot.log"
        },
        "strategies": [
            {"name": "MACD", "enabled": True}
        ]
    }
    d.write_text(yaml.dump(content))
    return str(d)


# 1. File not found
def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config("non_existent.yaml")


# 2. Missing iqoption section
def test_load_config_missing_iqoption_section(tmp_path):
    d = tmp_path / "bad.yaml"
    d.write_text(yaml.dump({"bot": {}}))
    with pytest.raises(ValueError, match="Missing required section: iqoption"):
        load_config(str(d))


# 3. Missing email
def test_load_config_missing_email(tmp_path):
    d = tmp_path / "bad.yaml"
    d.write_text(yaml.dump({"iqoption": {"password": "123"}}))
    with pytest.raises(ValueError, match="Missing required field: iqoption.email"):
        load_config(str(d))


# 4. Missing password
def test_load_config_missing_password(tmp_path):
    d = tmp_path / "bad.yaml"
    d.write_text(yaml.dump({"iqoption": {"email": "a@b.com"}}))
    with pytest.raises(ValueError, match="Missing required field: iqoption.password"):
        load_config(str(d))


# 5. Invalid account type
def test_load_config_invalid_account_type(tmp_path):
    d = tmp_path / "bad.yaml"
    d.write_text(yaml.dump({"iqoption": {"email": "a", "password": "b", "account_type": "DEMO"}}))
    with pytest.raises(ValueError, match="Invalid account_type"):
        load_config(str(d))


# 6. Invalid timeframe
def test_load_config_invalid_timeframe(tmp_path):
    d = tmp_path / "bad.yaml"
    content = {
        "iqoption": {"email": "a", "password": "b"},
        "bot": {"timeframe": 7}
    }
    d.write_text(yaml.dump(content))
    with pytest.raises(ValueError, match="Invalid timeframe"):
        load_config(str(d))


# 7. Trade amount too low
def test_load_config_trade_amount_too_low(tmp_path):
    d = tmp_path / "bad.yaml"
    content = {
        "iqoption": {"email": "a", "password": "b"},
        "bot": {"trade_amount": 0.5}
    }
    d.write_text(yaml.dump(content))
    with pytest.raises(ValueError, match="Minimum is 1.0"):
        load_config(str(d))


# 8. Invalid log level
def test_load_config_invalid_log_level(tmp_path):
    d = tmp_path / "bad.yaml"
    content = {
        "iqoption": {"email": "a", "password": "b"},
        "logging": {"level": "VERBOSE"}
    }
    d.write_text(yaml.dump(content))
    with pytest.raises(ValueError, match="Invalid logging level"):
        load_config(str(d))


# 9. Valid minimal
def test_load_config_valid_minimal(minimal_yaml):
    config = load_config(minimal_yaml)
    assert isinstance(config, BotConfig)
    assert config.iqoption.email == "test@example.com"
    # Defaults
    assert config.iqoption.account_type == "PRACTICE"
    assert config.bot.asset == "EURUSD"
    assert config.bot.dry_run is True


# 10. Valid full
def test_load_config_valid_full(full_yaml):
    config = load_config(full_yaml)
    assert config.iqoption.email == "full@example.com"
    assert config.iqoption.account_type == "REAL"
    assert config.bot.timeframe == 300
    assert config.bot.asset == "EURUSD"
    assert config.bot.dry_run is False
    assert config.logging.level == "DEBUG"
    assert config.logging.file == "bot.log"
    assert len(config.strategies) == 1


# 11. Dry run default True
def test_load_config_dry_run_default_true(minimal_yaml):
    config = load_config(minimal_yaml)
    assert config.bot.dry_run is True


# 12. Practice account default
def test_load_config_practice_account_default(minimal_yaml):
    config = load_config(minimal_yaml)
    assert config.iqoption.account_type == "PRACTICE"


# 13. Example config is valid
def test_example_config_is_valid(tmp_path):
    from pathlib import Path
    example_path = Path("config.yaml.example")
    if not example_path.exists():
        pytest.skip("config.yaml.example not found")

    content = example_path.read_text()
    content = content.replace("your_email@example.com", "test@test.com")
    content = content.replace("your_password", "testpass123")

    d = tmp_path / "config.yaml"
    d.write_text(content)

    config = load_config(str(d))
    assert isinstance(config, BotConfig)
    assert config.iqoption.email == "test@test.com"
    assert config.bot.asset == "EURUSD"
