# CHANGELOG — JCBV-NEXUS SDK

## [9.1.000] — 2026-04-30
### Sprint 17 — Final Cleanup
- Restructured tests/, created examples/, bumped version to 9.1.000
### Sprint 18 — Security & Repo Surgery
- Removed PII from repository, consolidated integration suite
### Sprint 19 — Technical Debt Zero
- Fixed flaky test, removed legacy build files, fixed httpx SSL warning

NOTE: El commit message "v9.0.000 Beta 003" fue un error tipográfico. La versión correcta es 9.1.000.

## [9.0.000] — 2026-04-29 — RELEASE OFICIAL

### Breaking Changes
- Ninguno. API pública idéntica a v8.x.

### Added
- Suite de tests profesional reorganizada por capas (core/, stealth/, trading/, streams/, strategy/, infrastructure/, regression/).
- `tests/unit/stealth/test_headers.py`: verificación de fingerprinting Chrome 124.
- `docs/api-reference.md`: referencia completa de métodos públicos.
- `docs/testing-guide.md`: guía detallada de ejecución de tests.

### Changed
- `tests/` reestructurado: eliminados nombres con referencia a sprints, subcarpetas por dominio.
- `docs/` saneado: reportes históricos movidos a `docs/archive/`.
- Versión incrementada a 9.0.000.

### Fixed
- `test_spinloop_migration.py` + `test_spinloop_remaining.py` fusionados en `tests/unit/regression/test_blocking_regression.py`.
- `test_suite_integration.py` movido de `unit/` a `integration/`.

### Security
- `test_headers.py`: garantía automatizada de fingerprint Chrome 124 e identidad HTTP==WS User-Agent.

## [8.9.995] — Sprint 12 — 2026-04-29
### Added
- Feature flag `ENABLE_IP_ROTATION` para activar/desactivar rotación IP (default: false).
- Soporte cross-platform para comandos `curl` (Linux/Windows).
- Documentación profesional: architecture.md y stealth-guide.md.

## [8.9.994] — Sprint 11 — 2026-04-28
### Fixed
- WebSocket handshake ahora incluye User-Agent y Origin (Chrome 124).
- SubscriptionManager reconectado a StreamsMixin (límite 15).
- CircuitBreaker integrado al flujo de reconexión para protección 429/403.

### Changed
- HTTP headers actualizados a Chrome 124.0.0.0.
- Accept-Language: es-419 para perfil LATAM.

## [8.9.993] — Sprint 10 — 2026-04-22
### Changed
- stable_api.py reducido de 1734 a 850 líneas (Refactor Mixins).
- Rate Limiter migrado a OrdersMixin y PositionsMixin.
- Estructura modular: core/, mixins/, strategy/.

## v8.9.999-PS7 (2026-04-28)
### Added
- `create_price_alert(active, price, direction)`: Support for creating server-side price alerts.
- `get_position_history()`: Retrieve closed trade history with filters.
- `get_open_positions(realtime_pnl=True)`: Real-time PnL tracking via `position-changed` handler.
- `_reconnect_with_backoff()`: Robust reconnection strategy with exponential backoff and jitter.
- `setup.py` & updated `pyproject.toml` for standard installation.

### Fixed
- Replaced `print()` statements with structured `logging`.
- Fixed synchronization gaps in `get_open_positions` snapshot.
- Enhanced `position_changed.py` to track dynamic PnL updates.

## v8.9.999-PS6 (2026-04-28)
### Added
- `HTTPXClient` with HTTP/2 support.
- Chrome 147 User-Agent parity for improved stealth.
- Reactive Handlers for `overnight-fee`, `alerts`, `short-active-info`, and `exchange-rate`.
- Background `TokenRefreshWorker` for session persistence.

## v8.9.999-PS5 (2026-04-28)
### Added
- Advanced Position Management: `set_trailing_stop`, `set_breakeven`.
- `sync_state_on_connect()` for robust recovery.
- Marginal trading stability fixes (4101 "Position Not Found" errors resolved).
