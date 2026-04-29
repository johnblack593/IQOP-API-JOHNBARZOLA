# JCBV-NEXUS Integration Test Report
**Fecha:** 2026-04-25 09:01:27 UTC  
**Duración total:** 171.2s  
**Versión SDK:** v8.9.950+  

## 🟡 SISTEMA AMARILLO — Minor Issues

| Métrica | Valor |
|---------|-------|
| Tests ejecutados | 60 |
| ✅ Pasaron | 53 (88.3%) |
| ❌ Fallaron | 6 |
| 💥 Errores | 1 |
| ⚠️ Warnings | 0 |

---

## Detalle por Capa

### ✅ L0 (23/23)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| import:IQ_Option (stable_api) | ✅ PASS | OK | 0.21s |
| import:API core (api.py) | ✅ PASS | OK | 0.0s |
| import:ServerClockSync (time_sync) | ✅ PASS | OK | 0.0s |
| import:Rate Limiter | ✅ PASS | OK | 0.0s |
| import:Idempotency Engine | ✅ PASS | OK | 0.0s |
| import:Correlation Engine | ✅ PASS | OK | 0.01s |
| import:Circuit Breaker | ✅ PASS | OK | 0.0s |
| import:Reconciler | ✅ PASS | OK | 0.0s |
| import:Reconnect Manager | ✅ PASS | OK | 0.0s |
| import:Candle Cache | ✅ PASS | OK | 0.0s |
| import:Asset Scanner | ✅ PASS | OK | 0.09s |
| import:Pattern Engine | ✅ PASS | OK | 0.01s |
| import:Market Quality | ✅ PASS | OK | 0.0s |
| import:Market Regime | ✅ PASS | OK | 0.0s |
| import:Martingale Guard | ✅ PASS | OK | 0.0s |
| import:Signal Consensus | ✅ PASS | OK | 0.0s |
| import:Performance Tracker | ✅ PASS | OK | 0.0s |
| import:Trade Journal | ✅ PASS | OK | 0.0s |
| import:Validator | ✅ PASS | OK | 0.0s |
| import:Expiration Helper | ✅ PASS | OK | 0.0s |
| import:ACTIVES Constants | ✅ PASS | OK | 0.0s |
| import:Config | ✅ PASS | OK | 0.0s |
| import:Logger | ✅ PASS | OK | 0.0s |

### ✅ L1 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| connect() | ✅ PASS | Conectado: None | 7.81s |
| change_balance(PRACTICE) | ✅ PASS | Balance PRACTICE: $9943.01 | 2.58s |
| get_profile_ansyc() | ✅ PASS | Profile recibido | 0.2s |

### ✅ L10 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| PatternEngine.analyze() | ✅ PASS | PatternEngine: 0 señales encontradas | 0.0s |
| MarketRegime.detect() | ✅ PASS | MarketRegime detectado: transitioning | 0.0s |
| SignalConsensus.get() | ✅ PASS | SignalConsensus module active | 0.0s |

### ⚠️ L11 (2/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| MartingaleGuard escalation | ❌ FAIL | Martingale debería escalar en pérdidas | 0.0s |
| MarketQuality.score() | ✅ PASS | MarketQuality tradeable: True | 0.0s |
| PerformanceTracker.stats() | ✅ PASS | PerformanceTracker: report generated ✓ | 0.0s |

### ✅ L12 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| TradeJournal log+read | ✅ PASS | TradeJournal: log OK ✓ | 0.0s |
| AssetScanner.scan() | ✅ PASS | AssetScanner module active | 0.0s |
| ReconnectManager config | ✅ PASS | ReconnectManager module active ✓ | 0.0s |

### ⚠️ L2 (5/6)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| get_all_open_time() | ✅ PASS | Tipos: ['binary', 'turbo', 'cfd', 'forex', 'crypto', 'digital'] \| Abiertos: 557 | 126.63s |
| ACTIVES KYC IDs | ✅ PASS | ACTIVES: 638 entradas \| KYC IDs verificados | 0.0s |
| get_all_profit() | ✅ PASS | Profits OK (284 activos) \| Muestra: [('SNAP-OTC', defaultdict(<class 'dict'>, {' | 0.44s |
| binary/turbo assets open | ✅ PASS | Binary/Turbo abiertos: 264 \| Primeros: ['TIAUSD-OTC', 'PEPEUSD-OTC', 'US30/JP225 | 0.0s |
| digital assets open | ✅ PASS | Digital abiertos: 164 \| Primeros: ['MSFT/AAPL-OTC', 'WIFUSD-OTC', 'GOOGLE-OTC'] | 0.0s |
| blitz assets open | ❌ FAIL | Ningún activo Blitz abierto (OTC debería estar disponible) | 0.0s |

### ✅ L3 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| time_sync módulo importable | ✅ PASS | Singleton _clock accesible | 0.0s |
| offset_seconds() razonable | ✅ PASS | Offset: 0.3695s | 3.0s |
| server_now() coherente | ✅ PASS | server.now() − time.time() = 0.3695s | 0.0s |

### ⚠️ L4 (1/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| TokenBucket consume/block | ❌ FAIL | TokenBucket: esperado 10 consumidos, got 0 | 0.0s |
| IdempotencyEngine dedup | ✅ PASS | IdempotencyRegistry: request registration functional ✓ | 0.0s |
| CorrelationEngine linkage | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

### ⚠️ L5 (2/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| buy() Turbo 1M | ✅ PASS | Turbo buy OK: asset=EURUSD-OTC order=13835702293 | 0.25s |
| check_win_v3() Turbo result | ❌ FAIL | check_win_v3() retornó None — timeout o trade no cerró | 0.02s |
| buy() Binary 1M | ✅ PASS | Binary buy OK: asset=GBPUSD-OTC order=13835702300 | 0.25s |

### ⚠️ L6 (1/2)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| buy_blitz() 30s | ❌ FAIL | Sin activos Blitz abiertos | 0.0s |
| clock offset post-Blitz | ✅ PASS | Clock offset post-Blitz: 0.3695s ✓ | 0.0s |

### ⚠️ L7 (1/2)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| Smart ID generator | ✅ PASS | Smart ID generado: do2107A20260425D090057T5MCSPT | 0.0s |
| buy_digital_spot() 5M | ❌ FAIL | buy_digital_spot() falló para EURUSD-OTC — id={'code': 'error_place_digital_orde | 0.27s |

### ✅ L8 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| get_candles() histórico | ✅ PASS | Candles OK: 10 velas de 1M para EURUSD-OTC | 0.23s |
| get_server_timestamp() | ✅ PASS | server_timestamp=1777107658.046 \| diff local=0.033s | 0.0s |
| start/stop candles stream | ✅ PASS | Realtime price EURUSD-OTC: defaultdict(<class 'dict'>, {}) | 23.18s |

### ✅ L9 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| CircuitBreaker state machine | ✅ PASS | CircuitBreaker: closed→open→half→closed OK ✓ | 6.0s |
| Reconciler register/resolve | ✅ PASS | Reconciler: instancia OK ✓ | 0.0s |
| Validator order params | ✅ PASS | Validator: valid=OK, invalid=rechazado ✓ | 0.0s |

---

## ❌ Fallas Detalladas

### `L2 — blitz assets open`
```
Ningún activo Blitz abierto (OTC debería estar disponible)
```

### `L4 — TokenBucket consume/block`
```
TokenBucket: esperado 10 consumidos, got 0
```

### `L5 — check_win_v3() Turbo result`
```
check_win_v3() retornó None — timeout o trade no cerró
```

### `L6 — buy_blitz() 30s`
```
Sin activos Blitz abiertos
```

### `L7 — buy_digital_spot() 5M`
```
buy_digital_spot() falló para EURUSD-OTC — id={'code': 'error_place_digital_order', 'message': 'invalid instrument'}
```

### `L11 — MartingaleGuard escalation`
```
Martingale debería escalar en pérdidas
```

### `L4 — CorrelationEngine linkage`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 306, in test_correlation
    engine.correlate(req_id, order_id=999)
    ^^^^^^^^^^^^^^^^
AttributeError: 'CorrelationEngine' object has no attribute 'correlate'

```

---

## Módulos del Sistema

| Módulo | Archivo | Tamaño |
|--------|---------|--------|
| `stable_api` | `iqoptionapi/stable_api.py` | — |
| `api` | `iqoptionapi/api.py` | — |
| `time_sync` | `iqoptionapi/time_sync.py` | — |
| `ratelimit` | `iqoptionapi/ratelimit.py` | — |
| `circuit_breaker` | `iqoptionapi/circuit_breaker.py` | — |
| `correlation_engine` | `iqoptionapi/correlation_engine.py` | — |
| `idempotency` | `iqoptionapi/idempotency.py` | — |
| `reconciler` | `iqoptionapi/reconciler.py` | — |
| `reconnect` | `iqoptionapi/reconnect.py` | — |
| `pattern_engine` | `iqoptionapi/pattern_engine.py` | — |
| `market_regime` | `iqoptionapi/market_regime.py` | — |
| `signal_consensus` | `iqoptionapi/signal_consensus.py` | — |
| `martingale_guard` | `iqoptionapi/martingale_guard.py` | — |
| `market_quality` | `iqoptionapi/market_quality.py` | — |
| `performance` | `iqoptionapi/performance.py` | — |
| `trade_journal` | `iqoptionapi/trade_journal.py` | — |
| `asset_scanner` | `iqoptionapi/asset_scanner.py` | — |
| `validator` | `iqoptionapi/validator.py` | — |

---
*Generado automáticamente por JCBV Integration Test Suite v1.0*