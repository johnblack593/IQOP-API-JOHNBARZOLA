# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [8.9.2] — 2026-04-20

### Added
- `pyproject.toml` (PEP 517/621) replacing legacy `setup.py`/`setup.cfg`
- `requirements-dev.txt` for development and testing environments
- `iqoptionapi/config.py` — single source of truth for all SDK constants
- `iqoptionapi/utils.py` — shared utilities (`nested_dict`)
- `.env.example` — documented environment variable contract
- `.github/workflows/ci.yml` — CI pipeline: ruff → mypy → pytest

### Changed
- `iqoptionapi/ratelimit.py` — `TokenBucket` defaults now reference `config.py`
- `iqoptionapi/reconnect.py` — `ReconnectManager` defaults now reference `config.py`
- `iqoptionapi/api.py` — `nested_dict` migrated to `utils.py`

### Fixed
- `pyrefly` `python_version` corrected from `3.9` to `3.11`
- `flake8`/`black` removed from production dependencies

### Removed
- `setup.py`, `setup.cfg`, `pyrefly.toml` — replaced by `pyproject.toml`
