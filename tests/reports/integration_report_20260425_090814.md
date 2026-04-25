# JCBV-NEXUS Integration Test Report
**Fecha:** 2026-04-25 09:11:03 UTC  
**Duración total:** 169.6s  
**Versión SDK:** v8.9.950+  

## 🟡 SISTEMA AMARILLO — Minor Issues

| Métrica | Valor |
|---------|-------|
| Tests ejecutados | 60 |
| ✅ Pasaron | 51 (85.0%) |
| ❌ Fallaron | 4 |
| 💥 Errores | 5 |
| ⚠️ Warnings | 0 |

---

## Detalle por Capa

### ✅ L0 (23/23)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| import:IQ_Option (stable_api) | ✅ PASS | OK | 0.25s |
| import:API core (api.py) | ✅ PASS | OK | 0.0s |
| import:ServerClockSync (time_sync) | ✅ PASS | OK | 0.0s |
| import:Rate Limiter | ✅ PASS | OK | 0.0s |
| import:Idempotency Engine | ✅ PASS | OK | 0.0s |
| import:Correlation Engine | ✅ PASS | OK | 0.0s |
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
| connect() | ✅ PASS | Conectado: None | 7.94s |
| change_balance(PRACTICE) | ✅ PASS | Balance PRACTICE: $9940.67 | 2.47s |
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
| get_all_open_time() | ✅ PASS | Tipos: ['binary', 'turbo', 'cfd', 'forex', 'crypto', 'digital'] \| Abiertos: 606 | 141.3s |
| ACTIVES KYC IDs | ✅ PASS | ACTIVES: 638 entradas \| KYC IDs verificados | 0.0s |
| get_all_profit() | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| binary/turbo assets open | ✅ PASS | Binary/Turbo abiertos: 293 \| Primeros: ['NFLX/AMZN-OTC', 'AUDNZD-OTC', 'DYDXUSD- | 0.0s |
| digital assets open | ✅ PASS | Digital abiertos: 156 \| Primeros: ['EURJPY-OTC', 'MU-OTC', 'USDBRL-OTC'] | 0.0s |
| blitz assets open | ❌ FAIL | Ningún activo Blitz abierto (OTC debería estar disponible) | 0.0s |

### ✅ L3 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| time_sync módulo importable | ✅ PASS | Singleton _clock accesible | 0.0s |
| offset_seconds() razonable | ✅ PASS | Offset: 0.3788s | 3.0s |
| server_now() coherente | ✅ PASS | server.now() − time.time() = 0.3788s | 0.0s |

### ✅ L4 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| TokenBucket consume/block | ✅ PASS | TokenBucket: overflow detectado OK ✓ | 0.0s |
| IdempotencyEngine dedup | ✅ PASS | IdempotencyRegistry: request registration functional ✓ | 0.0s |
| CorrelationEngine linkage | ✅ PASS | CorrelationEngine: get_correlation method found ✓ | 0.0s |

### ❌ L5 (0/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| buy() Turbo 1M | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| check_win_v3() Turbo result | ❌ FAIL | No hay order_id de Turbo para verificar | 0.0s |
| buy() Binary 1M | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

### ⚠️ L6 (1/2)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| buy_blitz() 30s | ❌ FAIL | Sin activos Blitz abiertos | 0.0s |
| clock offset post-Blitz | ✅ PASS | Clock offset post-Blitz: 0.3788s ✓ | 0.0s |

### ⚠️ L7 (1/2)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| Smart ID generator | ✅ PASS | Smart ID generado: do2107A20260425D091049T5MCSPT | 0.0s |
| buy_digital_spot() 5M | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 8.26s |

### ⚠️ L8 (1/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| get_candles() histórico | ❌ FAIL | get_candles() retornó vacío para EURUSD-OTC | 0.0s |
| get_server_timestamp() | ✅ PASS | server_timestamp=1777108258.061 \| diff local=0.204s | 0.0s |
| start/stop candles stream | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

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

### `L5 — check_win_v3() Turbo result`
```
No hay order_id de Turbo para verificar
```

### `L6 — buy_blitz() 30s`
```
Sin activos Blitz abiertos
```

### `L8 — get_candles() histórico`
```
get_candles() retornó vacío para EURUSD-OTC
```

### `L2 — get_all_profit()`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 211, in test_all_profits
    profits = self.api.get_all_profit()
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\stable_api.py", line 666, in get_all_profit
    init_info = self.get_all_init()
                ^^^^^^^^^^^^^^^^^^^
websocket._exceptions.WebSocketConnectionClosedException: Connection is already closed.

```

### `L5 — buy() Turbo 1M`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 334, in test_buy_turbo
    status, order_id = self.api.buy(TRADE_AMOUNT, asset, "call", 1)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ratelimit.py", line 100, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

```

### `L5 — buy() Binary 1M`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 355, in test_buy_binary
    status, order_id = self.api.buy(TRADE_AMOUNT, asset, "put", 1)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ratelimit.py", line 100, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

```

### `L7 — buy_digital_spot() 5M`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\stable_api.py", line 2224, in buy_digital_spot_v2
    request_id = self.api.place_digital_option_v2(instrument_id, active_id, amount)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\digital_option.py", line 60, in __call__
    self.send_websocket_request(self.name, data, request_id)
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\base.py", line 25, in send_websocket_request
    return self.api.send_websocket_request(name, msg,request_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
websocket._exceptions.WebSocketConnectionClosedException: Connection is already closed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 431, in test_buy_digital
    status, order_id = self.api.buy_digital_spot(asset, TRADE_AMOUNT, "call", 5)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ratelimit.py", line 100, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
websocket._exceptions.WebSocketConnectionClosedException: Connection is already closed.

```

### `L8 — start/stop candles stream`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 464, in test_realtime_price
    self.api.start_candles_one_stream(asset, 60)
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\stable_api.py", line 909, in start_candles_one_stream
    self.api.subscribe(OP_code.ACTIVES[ACTIVE], size)
websocket._exceptions.WebSocketConnectionClosedException: socket is already closed.

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