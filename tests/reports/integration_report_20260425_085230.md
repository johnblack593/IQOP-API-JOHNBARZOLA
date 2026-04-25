# JCBV-NEXUS Integration Test Report
**Fecha:** 2026-04-25 08:55:25 UTC  
**Duración total:** 174.4s  
**Versión SDK:** v8.9.950+  

## 🟠 SISTEMA NARANJA — Requires Attention

| Métrica | Valor |
|---------|-------|
| Tests ejecutados | 60 |
| ✅ Pasaron | 36 (60.0%) |
| ❌ Fallaron | 5 |
| 💥 Errores | 19 |
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
| import:Performance Tracker | ✅ PASS | OK | 0.01s |
| import:Trade Journal | ✅ PASS | OK | 0.0s |
| import:Validator | ✅ PASS | OK | 0.0s |
| import:Expiration Helper | ✅ PASS | OK | 0.0s |
| import:ACTIVES Constants | ✅ PASS | OK | 0.0s |
| import:Config | ✅ PASS | OK | 0.0s |
| import:Logger | ✅ PASS | OK | 0.0s |

### ✅ L1 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| connect() | ✅ PASS | Conectado: None | 8.23s |
| change_balance(PRACTICE) | ✅ PASS | Balance PRACTICE: $9944.01 | 2.65s |
| get_profile_ansyc() | ✅ PASS | Profile recibido | 0.2s |

### ❌ L10 (0/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| PatternEngine.analyze() | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| MarketRegime.detect() | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| SignalConsensus.get() | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

### ❌ L11 (0/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| MartingaleGuard escalation | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| MarketQuality.score() | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| PerformanceTracker.stats() | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

### ❌ L12 (0/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| TradeJournal log+read | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| AssetScanner.scan() | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| ReconnectManager config | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

### ⚠️ L2 (4/6)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| get_all_open_time() | ✅ PASS | Tipos: ['binary', 'turbo', 'cfd', 'forex', 'crypto', 'digital'] \| Abiertos: 559 | 150.54s |
| ACTIVES KYC IDs | ✅ PASS | ACTIVES: 638 entradas \| KYC IDs verificados | 0.0s |
| get_all_profit() | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| binary/turbo assets open | ✅ PASS | Binary/Turbo abiertos: 264 \| Primeros: ['ETHUSD-OTC', 'SNAP-OTC', 'WDC-OTC'] | 0.0s |
| digital assets open | ✅ PASS | Digital abiertos: 164 \| Primeros: ['AMAZON-OTC', 'TONUSD-OTC', 'IOTAUSD-OTC'] | 0.0s |
| blitz assets open | ❌ FAIL | Ningún activo Blitz abierto (OTC debería estar disponible) | 0.0s |

### ✅ L3 (3/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| time_sync módulo importable | ✅ PASS | Singleton _clock accesible | 0.0s |
| offset_seconds() razonable | ✅ PASS | Offset: 0.3658s | 3.0s |
| server_now() coherente | ✅ PASS | server.now() − time.time() = 0.3658s | 0.0s |

### ❌ L4 (0/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| TokenBucket consume/block | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| IdempotencyEngine dedup | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| CorrelationEngine linkage | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

### ❌ L5 (0/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| buy() Turbo 1M | ❌ FAIL | buy() Turbo falló — order_id=13835695686 | 2.5s |
| check_win_v3() Turbo result | ❌ FAIL | No hay order_id de Turbo para verificar | 0.0s |
| buy() Binary 1M | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

### ⚠️ L6 (1/2)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| buy_blitz() 30s | ❌ FAIL | Sin activos Blitz abiertos | 0.0s |
| clock offset post-Blitz | ✅ PASS | Clock offset post-Blitz: 0.3633s ✓ | 0.0s |

### ⚠️ L7 (1/2)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| Smart ID generator | ✅ PASS | Smart ID generado: do2107A20260425D085518T5MCSPT | 0.0s |
| buy_digital_spot() 5M | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 6.9s |

### ⚠️ L8 (1/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| get_candles() histórico | ❌ FAIL | get_candles() retornó vacío para EURUSD-OTC | 0.0s |
| get_server_timestamp() | ✅ PASS | server_timestamp=1777107325.3 \| diff local=0.300s | 0.0s |
| start/stop candles stream | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

### ❌ L9 (0/3)

| Test | Status | Detalle | Tiempo |
|------|--------|---------|--------|
| CircuitBreaker state machine | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| Reconciler register/resolve | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |
| Validator order params | 💥 ERROR | Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNB | 0.0s |

---

## ❌ Fallas Detalladas

### `L2 — blitz assets open`
```
Ningún activo Blitz abierto (OTC debería estar disponible)
```

### `L5 — buy() Turbo 1M`
```
buy() Turbo falló — order_id=13835695686
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
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 208, in test_all_profits
    profits = self.api.get_all_profit()
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\stable_api.py", line 666, in get_all_profit
    init_info = self.get_all_init()
                ^^^^^^^^^^^^^^^^^^^
websocket._exceptions.WebSocketConnectionClosedException: socket is already closed.

```

### `L4 — TokenBucket consume/block`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 281, in test_token_bucket
    bucket = TokenBucket(rate=10, capacity=10, block=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: TokenBucket.__init__() got an unexpected keyword argument 'rate'

```

### `L4 — IdempotencyEngine dedup`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 291, in test_idempotency
    from iqoptionapi.idempotency import IdempotencyEngine
ImportError: cannot import name 'IdempotencyEngine' from 'iqoptionapi.idempotency' (D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\idempotency.py)

```

### `L4 — CorrelationEngine linkage`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 304, in test_correlation
    engine = CorrelationEngine()
             ^^^^^^^^^^^^^^^^^^^
TypeError: CorrelationEngine.__init__() missing 1 required positional argument: 'candle_cache'

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
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\stable_api.py", line 2223, in buy_digital_spot_v2
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

### `L9 — CircuitBreaker state machine`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 482, in test_circuit_breaker
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: CircuitBreaker.__init__() got an unexpected keyword argument 'failure_threshold'

```

### `L9 — Reconciler register/resolve`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 497, in test_reconciler
    rec = Reconciler()
          ^^^^^^^^^^^^
TypeError: Reconciler.__init__() missing 1 required positional argument: 'api_instance'

```

### `L9 — Validator order params`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 512, in test_validator
    ok, err = v.validate_order(asset="EURUSD-OTC", amount=1.0,
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Validator.validate_order() got an unexpected keyword argument 'asset'

```

### `L10 — PatternEngine.analyze()`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 538, in test_pattern_engine
    pe = PatternEngine()
         ^^^^^^^^^^^^^^^
TypeError: PatternEngine.__init__() missing 1 required positional argument: 'candle_cache'

```

### `L10 — MarketRegime.detect()`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 548, in test_market_regime
    mr = MarketRegime()
         ^^^^^^^^^^^^^^
TypeError: MarketRegime.__init__() missing 1 required positional argument: 'candle_cache'

```

### `L10 — SignalConsensus.get()`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 558, in test_signal_consensus
    sc.add_signal(source="pattern", direction="call", strength=0.7)
    ^^^^^^^^^^^^^
AttributeError: 'SignalConsensus' object has no attribute 'add_signal'

```

### `L11 — MartingaleGuard escalation`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 576, in test_martingale_guard
    amounts = [mg.next_amount(result) for result in
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 576, in <listcomp>
    amounts = [mg.next_amount(result) for result in
               ^^^^^^^^^^^^^^^^^^^^^^
TypeError: MartingaleGuard.next_amount() missing 1 required positional argument: 'current_balance'

```

### `L11 — MarketQuality.score()`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 585, in test_market_quality
    from iqoptionapi.market_quality import MarketQuality
ImportError: cannot import name 'MarketQuality' from 'iqoptionapi.market_quality' (D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\market_quality.py)

```

### `L11 — PerformanceTracker.stats()`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 595, in test_performance
    pt = PerformanceTracker()
         ^^^^^^^^^^^^^^^^^^^^
TypeError: PerformanceTracker.__init__() missing 1 required positional argument: 'trade_journal'

```

### `L12 — TradeJournal log+read`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 616, in test_trade_journal
    tj = TradeJournal(path=":memory:")  # sin archivo real
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: TradeJournal.__init__() got an unexpected keyword argument 'path'

```

### `L12 — AssetScanner.scan()`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 628, in test_asset_scanner
    results = scanner.scan(categories=["turbo"], min_profit=0.7)
              ^^^^^^^^^^^^
AttributeError: 'AssetScanner' object has no attribute 'scan'

```

### `L12 — ReconnectManager config`
```
Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 73, in _run
    detail = fn()
             ^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\test_suite_integration.py", line 634, in test_reconnect_module
    rm = ReconnectManager(max_retries=3, base_delay=1.0)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: ReconnectManager.__init__() got an unexpected keyword argument 'max_retries'

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