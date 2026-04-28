# JCBV-NEXUS Integration Test Report
**Fecha:** 2026-04-25 09:15:35 UTC  
**Duración total:** 203.1s  
**Versión SDK:** v8.9.950+  

## 🟡 SISTEMA AMARILLO — Minor Issues

| Métrica | Valor |
|---------|-------|
| Tests ejecutados | 60 |
| ✅ Pasaron | 53 (88.3%) |
| ❌ Fallaron | 6 |
| 💥 Errores | 1 |
| ⚠️ Warnings | 1 |

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
| import:Correlation Engine | ✅ PASS | OK | 0.0s |
| import:Circuit Breaker | ✅ PASS | OK | 0.0s |
| import:Reconciler | ✅ PASS | OK | 0.0s |
| import:Reconnect Manager | ✅ PASS | OK | 0.0s |
| import:Candle Cache | ✅ PASS | OK | 0.0s |
| import:Asset Scanner | ✅ PASS | OK | 0.1s |
| import:Pattern Engine | ✅ PASS | OK | 0.0s |
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
| connect() | ✅ PASS | Conectado: None | 8.35s |
| change_balance(PRACTICE) | ✅ PASS | Balance PRACTICE: $9942.50 | 2.56s |
| get_profile_ansyc() | ✅ PASS | Profile recibido | 0.19s |

### ✅ L10 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| PatternEngine.analyze() | ✅ PASS | PatternEngine: 0 señales encontradas | 0.0s |
| MarketRegime.detect() | ✅ PASS | MarketRegime detectado: transitioning | 0.0s |
| SignalConsensus.get() | ✅ PASS | SignalConsensus module active | 0.0s |

### ✅ L11 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| MartingaleGuard escalation | ✅ PASS | MartingaleGuard: amounts=[1.0, 2.0, 4.0] ✓ | 0.0s |
| MarketQuality.score() | ✅ PASS | MarketQuality tradeable: True | 0.0s |
| PerformanceTracker.stats() | ✅ PASS | PerformanceTracker: report generated ✓ | 0.0s |

### ✅ L12 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| TradeJournal log+read | ✅ PASS | TradeJournal: log OK ✓ | 0.0s |
| AssetScanner.scan() | ✅ PASS | AssetScanner module active | 0.0s |
| ReconnectManager config | ✅ PASS | ReconnectManager module active ✓ | 0.0s |

### ⚠️ L2 (4/6)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| get_all_open_time() | ✅ PASS | Tipos: ['binary', 'turbo', 'cfd', 'forex', 'crypto', 'digital'] \| Abiertos: 607 | 128.27s |
| ACTIVES KYC IDs | ✅ PASS | ACTIVES: 638 entradas \| KYC IDs verificados | 0.0s |
| get_all_profit() | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| binary/turbo assets open | ✅ PASS | Binary/Turbo abiertos: 293 \| Primeros: ['CADCHF-OTC', 'MU-OTC', 'GRTUSD-OTC'] | 0.0s |
| digital assets open | ✅ PASS | Digital abiertos: 156 \| Primeros: ['ONDOUSD-OTC', 'SNDK-OTC', 'NVDA-OTC'] | 0.0s |
| blitz assets open | ❌ FAIL | Ningún activo Blitz abierto (OTC debería estar disponible) | 0.0s |

### ✅ L3 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| time_sync módulo importable | ✅ PASS | Singleton _clock accesible | 0.0s |
| offset_seconds() razonable | ✅ PASS | Offset: 0.3790s | 3.0s |
| server_now() coherente | ✅ PASS | server.now() − time.time() = 0.3790s | 0.0s |

### ✅ L4 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| TokenBucket consume/block | ✅ PASS | TokenBucket: overflow detectado OK ✓ | 0.0s |
| IdempotencyEngine dedup | ✅ PASS | IdempotencyRegistry: request registration functional ✓ | 0.0s |
| CorrelationEngine linkage | ✅ PASS | CorrelationEngine: get_correlation method found ✓ | 0.0s |

### ❌ L5 (0/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| buy() Turbo 1M | ❌ FAIL | buy() Turbo falló — order_id=None | 15.61s |
| check_win_v3() Turbo result | ❌ FAIL | No hay order_id de Turbo para verificar | 0.0s |
| buy() Binary 1M | ❌ FAIL | buy() Binary falló — order_id=None | 15.05s |

### ⚠️ L6 (1/2)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| buy_blitz() 30s | ❌ FAIL | Sin activos Blitz abiertos | 0.0s |
| clock offset post-Blitz | ✅ PASS | Clock offset post-Blitz: 0.3796s ✓ | 0.0s |

### ⚠️ L7 (1/2)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| Smart ID generator | ✅ PASS | Smart ID generado: do2107A20260425D091505T5MCSPT | 0.0s |
| buy_digital_spot() 5M | ❌ FAIL | buy_digital_spot() falló para EURUSD-OTC — id={'code': 'error_place_digital_orde | 0.28s |

### ✅ L8 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| get_candles() histórico | ✅ PASS | Candles OK: 10 velas de 1M para EURUSD-OTC | 0.23s |
| get_server_timestamp() | ✅ PASS | server_timestamp=1777108506.212 \| diff local=0.298s | 0.0s |
| start/stop candles stream | ✅ PASS | Realtime price EURUSD-OTC: defaultdict(<class 'dict'>, {}) | 23.21s |

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

### `L5 — buy() Turbo 1M`
```
buy() Turbo falló — order_id=None
```

### `L5 — check_win_v3() Turbo result`
```
No hay order_id de Turbo para verificar
```

### `L5 — buy() Binary 1M`
```
buy() Binary falló — order_id=None
```

### `L6 — buy_blitz() 30s`
```
Sin activos Blitz abiertos
```

### `L7 — buy_digital_spot() 5M`
```
buy_digital_spot() falló para EURUSD-OTC — id={'code': 'error_place_digital_order', 'message': 'invalid instrument'}
```

### `L2 — get_all_profit()`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 209, in test_all_profits
    print("  ⚠️ Reconnecting for L2 tests...")
  File "C:\Users\JCBV\AppData\Local\Programs\Python\Python311\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode characters in position 2-3: character maps to <undefined>

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