# Changelog
All notable changes to JCBV-NEXUS are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com)

---

## [9.3.333] — 2026-05-03

### Summary
Production-ready release of the JCBV-NEXUS IQ Option SDK.
Complete bot automation stack with 382 unit tests, CLI,
backtest engine, circuit breaker, and trade journaling.

### Added
- **BotOrchestrator** — async trading loop with dry-run mode
  and configurable candle window (S8-T1)
- **CircuitBreaker integration** — drawdown guard and
  consecutive-loss protection in orchestrator (S8-T2)
- **TradeJournal integration** — async post-trade recording
  via daemon thread, non-blocking main loop (S8-T2)
- **CLI entry point** (`iqopt`) with YAML config loader,
  strict schema validation and dataclass mapping (S9-T1)
- **CLI subcommands**: `run`, `backtest`, `status`,
  `version` with argparse subparsers (S9-T2)
- **bot_state.json** — live state file written on run,
  deleted on clean shutdown (S9-T2)
- **README.md** — professional documentation with ASCII
  architecture diagram, CLI reference, indicator table (S10-T1)
- **config.yaml.example** — annotated configuration
  template with all supported parameters (S10-T1)

### Fixed
- ruff E402: moved `import threading` to module level in
  test_orchestrator.py (S10-T2)
- pip-audit CI: added --skip-editable flag to skip local
  package not published on PyPI (S10-T2)

### Changed
- Version bumped from 9.3.x → 9.3.333

### Test Coverage
- 382 unit tests | 5 skipped (pyarrow optional)
- 59% line coverage across 160 modules
- 0 ruff errors | 0 security vulnerabilities (audited deps)

---

## [9.3.x] — Sprint 8–9 (Internal)
Bot automation layer built on top of v9.2.x SDK.

## [9.2.x] — Sprints 5–7 (Internal)
Backtest engine, indicators, strategy registry, MTF pipeline.

## [9.1.x] — Sprints 1–4 (Internal)
SDK refactor: rate limiting, reconnect, circuit breaker,
asset taxonomy, trade journal, health endpoint.
