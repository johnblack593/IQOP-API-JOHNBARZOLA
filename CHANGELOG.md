# CHANGELOG

Todos los cambios notables de este proyecto. Formato: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

***

## [2.0.0] — 2026-04-22 — "API con esteroides"

### 🔴 Crítico — Bug fixes de runtime

- **fix(digital):** Corregido `AttributeError` en `buy_digital_spot()` y
`sell_digital_option()` por referencia rota a `self._rate_limiter` →
migrado a `self._order_bucket` con decorador `@rate_limited`
- **fix(spinloop):** Eliminados todos los `while True` en lógica de espera de trades.
`check_win*()` ahora usa `threading.Event + timeout` — retorna `None` en lugar de
congelar el robot indefinidamente
- **fix(spinloop):** Migrados streams de candles y mood a `Event.wait(timeout=20s)`
- **fix(hardening):** Timeouts de seguridad (15s) en `get_strike_list`,
`get_digital_position`, `close_position_v2`
- **fix(cache):** `candle_cache.py` reemplaza dict sin límite por `deque(maxlen=500)`
— elimina memory leak garantizado en bots de larga duración
- **fix(init):** Deduplicado `get_all_init()` — una sola llamada WS por sesión
con guard `_init_data_received`
- **fix(digital):** Corregido formato de `instrument_id` en `buy_digital_spot_v2()`
al estándar: `do{ASSET}{YYYYMMDDHHMM}PT{DUR}M{DIR}SPT`
- **fix(buy):** Corregido typo `buyv3_by_raw_expirations` → `buyv3_by_raw_expired`

### ✅ Nuevas funcionalidades — Portfolio control

- **feat(portfolio):** `get_open_positions(instrument_type)` — snapshot de trades vivos
- **feat(portfolio):** `get_all_open_positions()` — todos los tipos en paralelo
- **feat(reconciler):** `reconcile_missed_results(since_ts)` — recupera resultados
de trades expirados durante una desconexión (betinfo + position-history fallback)
- **feat(portfolio):** `get_order_status(order_id, type)` — dispatcher genérico
normalizado para binary/digital/CFD

### ✅ Nuevas funcionalidades — Instrumentos de trading

- **feat(trading):** `buy_blitz()` — soporte completo de Blitz options via
`initialization-data` (nunca via `get_instruments("blitz")`)
- **feat(digital):** `buy_digital_spot_v2()` certificado contra servidor real
- **feat(candles):** `subscribe_candle_v2(active, size, buffer_max, on_candle)` —
suscripción con buffer acotado y callback async-safe

### ✅ Nuevas funcionalidades — Inteligencia de mercado

- **feat(intelligence):** `MarketQualityMonitor` — spread/slippage monitor.
`is_tradeable()` para filtrar activos antes de operar
- **feat(intelligence):** `PatternEngine` — 6 patrones de velas: DOJI, HAMMER,
SHOOTING_STAR, BULLISH_ENGULFING, BEARISH_ENGULFING, INSIDE_BAR
- **feat(intelligence):** `MarketRegime` — ADX simplificado para detectar
trending/ranging/transitioning. Incluye `get_trend_direction()`
- **feat(intelligence):** `CorrelationEngine` — Pearson inter-activos sin numpy.
`get_correlated_assets()` para gestión de riesgo de portafolio
- **feat(scanner):** `AssetScanner.get_best_payout_assets()` — top activos por
payout filtrados por calidad y régimen de mercado
- **feat(performance):** `PerformanceTracker.get_asset_score()` — win rate, EV,
profit factor por activo+timeframe

### ✅ Infraestructura y calidad

- **feat(wiring):** 13 módulos wired automáticamente en `IQ_Option.__init__`
- **feat(validation):** Gate de `validator.validate_order()` en todos los `buy_*`
- **feat(journal):** `trade_journal.record()` auto-llamado en todos los `check_win*`
- **feat(ws):** Circuit completado — `result_event_store` y
`position_changed_event_store` reciben `.set()` en handlers WS
- **test:** Suite de 13 tests unitarios con mocks WS — sin credenciales reales
- **ci:** GitHub Actions con lint (ruff) + test (pytest)
- **chore:** Migrado `setup.py` → `pyproject.toml` (PEP 517/518)

### Módulos nuevos en esta versión
`security.py` · `reconnect.py` · `ratelimit.py` · `idempotency.py` · `logger.py`
`config.py` · `expiration.py` · `constants.py` · `circuit_breaker.py`
`martingale_guard.py` · `signal_consensus.py` · `candle_cache.py` · `asset_scanner.py`
`trade_journal.py` · `validator.py` · `performance.py` · `session_scheduler.py`
`reconciler.py` · `market_quality.py` · `pattern_engine.py` · `market_regime.py`
`correlation_engine.py`
`ws/objects/portfolio_positions.py` · `ws/received/portfolio_get_positions.py`

***

## [1.x.x] — Legacy

Versión original del fork público. Sin módulos de inteligencia. Bugs de runtime
activos en digital options y check_win. Ver historial de git para detalles.
