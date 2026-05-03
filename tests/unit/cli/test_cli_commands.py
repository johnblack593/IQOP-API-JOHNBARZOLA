"""
tests/unit/cli/test_cli_commands.py
──────────────────────────────────
Pruebas para los subcomandos de la CLI.
"""
from __future__ import annotations

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import yaml

from iqoptionapi.cli.main import main


@pytest.fixture
def mock_config_file(tmp_path):
    config = tmp_path / "config.yaml"
    content = {
        "iqoption": {"email": "test", "password": "test"},
        "bot": {"asset": "EURUSD", "trade_amount": 10.0}
    }
    config.write_text(yaml.dump(content))
    return str(config)


# 1. version command
def test_version_command_prints_output(capsys):
    with patch("sys.argv", ["iqopt", "version"]):
        main()
    captured = capsys.readouterr()
    assert "JCBV-NEXUS v9.3" in captured.out
    assert "Python" in captured.out


# 2. no command prints help
def test_no_command_exits_zero(capsys):
    with patch("sys.argv", ["iqopt"]):
        with pytest.raises(SystemExit) as e:
            main()
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "usage: iqopt" in captured.out


# 3. run command calls launch
@patch("iqoptionapi.cli.main._launch_bot")
@patch("iqoptionapi.cli.main.load_config")
def test_run_command_loads_config_and_calls_launch(mock_load, mock_launch, mock_config_file):
    cfg = MagicMock()
    cfg.logging.level = "INFO"
    cfg.logging.file = None
    mock_load.return_value = cfg
    with patch("sys.argv", ["iqopt", "run", "--config", mock_config_file]):
        main()
    mock_load.assert_called_once()
    mock_launch.assert_called_once()


# 4. run config not found
def test_run_command_config_not_found_exits_1(capsys):
    with patch("sys.argv", ["iqopt", "run", "--config", "missing.yaml"]):
        with pytest.raises(SystemExit) as e:
            main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.err


# 5. backtest data not found
def test_backtest_data_file_not_found_exits_1(capsys, mock_config_file):
    with patch("sys.argv", ["iqopt", "backtest", "-c", mock_config_file, "-d", "no.csv"]):
        with pytest.raises(SystemExit) as e:
            main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Data file not found" in captured.err


# 6. backtest runs engine
@patch("iqoptionapi.backtest.engine.BacktestEngine.run")
def test_backtest_reads_csv_and_runs_engine(mock_run, tmp_path, mock_config_file, capsys):
    csv = tmp_path / "data.csv"
    # Need 30 candles
    rows = ["time,open,high,low,close,volume"]
    for i in range(30):
        rows.append(f"{i},1.1,1.2,1.0,1.1,100")
    csv.write_text("\n".join(rows))
    
    # Mock result
    res = MagicMock()
    res.strategy_name = "DummyHold"
    res.total_candles = 30
    res.total_trades = 0
    res.win_rate = 0.0
    res.profit_factor = 0.0
    res.sharpe_ratio = 0.0
    res.max_drawdown_pct = 0.0
    res.expectancy = 0.0
    res.initial_balance = 1000.0
    res.final_balance = 1000.0
    mock_run.return_value = res
    
    with patch("sys.argv", ["iqopt", "backtest", "-c", mock_config_file, "-d", str(csv)]):
        main()
    
    mock_run.assert_called_once()
    captured = capsys.readouterr()
    assert "BACKTEST REPORT" in captured.out


# 7. backtest writes json
@patch("iqoptionapi.backtest.engine.BacktestEngine.run")
def test_backtest_writes_json_output(mock_run, tmp_path, mock_config_file):
    csv = tmp_path / "data.csv"
    rows = ["time,open,high,low,close,volume"]
    for i in range(30):
        rows.append(f"{i},1.1,1.2,1.0,1.1,100")
    csv.write_text("\n".join(rows))
    out = tmp_path / "report.json"
    
    res = MagicMock()
    res.strategy_name = "Test"
    res.total_candles = 30
    res.total_trades = 0
    res.win_rate = 0.0
    res.profit_factor = 0.0
    res.sharpe_ratio = 0.0
    res.max_drawdown_pct = 0.0
    res.expectancy = 0.0
    res.initial_balance = 100.0
    res.final_balance = 100.0
    mock_run.return_value = res
    
    with patch("sys.argv", ["iqopt", "backtest", "-c", mock_config_file, "-d", str(csv), "-o", str(out)]):
        main()
    
    assert os.path.exists(out)
    with open(out, "r") as f:
        data = json.load(f)
    assert data["strategy_name"] == "Test"


# 8. status bot not running
def test_status_bot_not_running(capsys):
    with patch("sys.argv", ["iqopt", "status", "--state-file", "none.json"]):
        main()
    captured = capsys.readouterr()
    assert "Bot is not running." in captured.out


# 9. status reads state file
def test_status_reads_state_file(tmp_path, capsys):
    state = tmp_path / "state.json"
    data = {
        "pid": 1234,
        "started_at": "2026-01-01",
        "asset": "EURUSD",
        "timeframe": 60,
        "dry_run": True,
        "trade_count": 5,
        "last_tick": "now"
    }
    state.write_text(json.dumps(data))
    
    with patch("sys.argv", ["iqopt", "status", "--state-file", str(state)]):
        main()
    
    captured = capsys.readouterr()
    assert "PID:          1234" in captured.out
    assert "Asset:        EURUSD @ 60s" in captured.out


# 10. status missing file no exception
def test_status_missing_state_file_no_exception(capsys):
    # Ya cubierto por test_status_bot_not_running, pero por si acaso
    with patch("sys.argv", ["iqopt", "status", "--state-file", "definitely_not_here.json"]):
        try:
            main()
        except Exception as e:
            pytest.fail(f"status command raised exception: {e}")
    captured = capsys.readouterr()
    assert "Bot is not running." in captured.out
