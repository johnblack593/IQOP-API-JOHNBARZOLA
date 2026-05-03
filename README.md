# JCBV-NEXUS — IQ Option Trading Bot SDK

![Python](https://img.shields.io/badge/python-3.11.9-blue)
![Tests](https://img.shields.io/badge/tests-381%20passed-green)
![License](https://img.shields.io/badge/license-MIT-green)

JCBV-NEXUS is a professional-grade IQ Option API SDK designed for high-frequency algorithmic trading and resilient market interaction. It provides a robust infrastructure for building, testing, and deploying trading bots with a focus on security, performance, and risk management.

Designed primarily for **PRACTICE** accounts, the SDK includes sophisticated mechanisms for signal consensus, circuit breaking, and asynchronous journaling, ensuring that your trading strategies are executed safely and documented thoroughly.

## Architecture

The SDK follows a modular design, decoupling connection handling from trading logic and risk management:

```text
  IQ Option Server
        │ WebSocket
        ▼
  ┌─────────────┐    ┌──────────────────┐
  │  stable_api │───▶│ BotOrchestrator  │
  └─────────────┘    └────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │SignalConsensus│ │CircuitBreaker│ │ TradeJournal │
      └──────┬───────┘ └──────────────┘ └──────────────┘
             │
      ┌──────▼───────────────────────┐
      │  indicators.py (12 indicators)│
      │  VWAP·OBV·ADX·%R·CCI·...    │
      └──────────────────────────────┘
```

## Requirements

- **Python**: 3.11.9+
- **Core Dependencies**:
  - `websocket-client`: Real-time data streaming.
  - `requests` & `httpx`: REST API interactions.
  - `numpy`: Fast numerical analysis for indicators and backtesting.
  - `PyYAML`: Configuration management.

## Installation

### From Source
```bash
git clone https://github.com/johnblack593/IQOP-API-JOHNBARZOLA.git
cd IQOP-API-JOHNBARZOLA
pip install -e ".[dev]"
```

### Verify Installation
```bash
python -c "from iqoptionapi.stable_api import IQ_Option; print('OK')"
iqopt version
```

## Quick Start

### 1. Create Config File
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your email and password
```

### 2. Run in Simulation (Dry-Run)
```bash
iqopt run --config config.yaml --dry-run
```

### 3. Run Backtest
```bash
iqopt backtest --config config.yaml --data data/eurusd_1m.csv
```

### 4. Check Status
```bash
iqopt status
```

## CLI Reference

| Command | Description | Key Flags |
|---------|-------------|-----------|
| `iqopt run` | Launch trading bot | `--config`, `--dry-run` |
| `iqopt backtest` | Offline strategy test | `--config`, `--data`, `--output` |
| `iqopt status` | Show bot process state | `--state-file` |
| `iqopt version` | Print version info | — |

## Indicators Available

The SDK provides a rich set of 12 technical indicators implemented in `iqoptionapi/strategy/indicators.py`:

| Indicator | Category | Description |
|-----------|----------|-------------|
| SMA | Trend | Simple Moving Average |
| EMA | Trend | Exponential Moving Average |
| RSI | Momentum | Relative Strength Index |
| MACD | Momentum | Moving Average Convergence Divergence |
| Bollinger Bands | Volatility | Standard deviation bands |
| Stochastic | Momentum | %K/%D oscillator |
| ATR | Volatility | Average True Range |
| VWAP | Volume | Volume Weighted Average Price |
| OBV | Volume | On-Balance Volume |
| ADX | Trend | Average Directional Index |
| Williams %R | Momentum | Williams Percent Range |
| CCI | Momentum | Commodity Channel Index |

## BacktestEngine Usage

You can use the `BacktestEngine` directly in your Python scripts for custom simulation workflows:

```python
from iqoptionapi.backtest.engine import BacktestEngine
from iqoptionapi.strategy.base import BaseStrategy
import numpy as np

# Load your historical data
candles = np.loadtxt("data.csv", delimiter=",", skiprows=1, dtype=float)

# Initialize engine
engine = BacktestEngine(
    strategy=MyCustomStrategy(...),
    candles=candles,
    initial_balance=1000.0,
    trade_amount=10.0,
    payout=0.82,
)

# Run simulation
result = engine.run()

print(f"Win Rate: {result.win_rate:.1%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown_pct:.1f}%")
```

## Safety Features

- **Circuit Breaker**: Automatically halts the bot if drawdown thresholds or consecutive loss limits are exceeded.
- **Dry-Run Mode**: Defaults to `True`. The bot will never place real trades unless explicitly configured.
- **Asynchronous Journaling**: Records all trade results (including post-expiration verification) without blocking the main execution loop.
- **Input Validation**: Robust handling of `NaN` and edge cases across all technical indicators.
- **Comprehensive Testing**: 381+ unit tests ensuring stability and correctness.

## Project Structure

```text
IQOP-API-JOHNBARZOLA/
├── iqoptionapi/
│   ├── backtest/          # BacktestEngine + metrics
│   ├── bot/               # BotOrchestrator
│   ├── cli/               # CLI (main.py, config_loader.py)
│   ├── strategy/          # indicators, signals, consensus
│   │   ├── indicators.py  # 12 technical indicators
│   │   ├── signal_consensus.py
│   │   └── server_indicator_bridge.py
│   └── ws/                # WebSocket receivers
├── tests/
│   └── unit/              # 381+ tests
├── config.yaml.example
└── pyproject.toml
```

## License

This project is licensed under the MIT License - see the [pyproject.toml](pyproject.toml) file for details.
