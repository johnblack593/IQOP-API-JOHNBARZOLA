# TRADING VALIDATION REPORT

## SECCIÓN 0: METADATA DE EJECUCIÓN
- **Fecha Inicio:** 2026-05-03T12:04:07.178219
- **Fecha Fin:** 2026-05-03T12:04:38.139422
- **Duración Total:** 31.0 segundos
- **Versión SDK:** 9.3.721
- **Cuenta usada:** PRACTICE ✅
- **Balance Inicial:** $9997.44
- **Balance Final:** $0.00
- **Net P&L:** $-9997.44

## SECCIÓN 1: RESUMEN EJECUTIVO
| GRUPO | SUBCATEGORÍA | ACTIVO USADO | OPS | WIN | LOSS | SKIP | TIMEOUT | ERROR | TASA ÉXITO SDK |
|-------|--------------|--------------|-----|-----|------|------|---------|-------|----------------|
| A | Blitz | EURUSD-OTC | 2 | 0 | 0 | 0 | 2 | 0 | 100% ✅ |
| A | Binary | EURUSD-OTC | 2 | 0 | 0 | 0 | 0 | 2 | 0% ❌ |
| A | Digital | BTCUSD | 2 | 0 | 0 | 0 | 0 | 2 | 0% ❌ |
| B | Forex | BTCUSD | 2 | 0 | 0 | 0 | 0 | 2 | 0% ❌ |
| B | Stocks | MSFT | 2 | 0 | 0 | 0 | 0 | 2 | 0% ❌ |
| B | Crypto | BTCUSD | 2 | 0 | 0 | 0 | 0 | 2 | 0% ❌ |
| B | Commodity | Gold | 2 | 0 | 0 | 0 | 0 | 2 | 0% ❌ |
| B | Index | US30 | 2 | 0 | 0 | 0 | 0 | 2 | 0% ❌ |
| B | Etf | BTCUSD | 2 | 0 | 0 | 0 | 0 | 2 | 0% ❌ |

## SECCIÓN 2: DETALLE FORENSE POR OPERACIÓN
### [A.1] Blitz — EURUSD-OTC — CALL
| Campo | Valor |
|-------|-------|
| Order ID | True |
| Asset | EURUSD-OTC |
| Type | binary |
| Direction | CALL |
| Amount | $1.00 |
| Duration | 60s |
| Open Price | N/A |
| Close Price | N/A |
| Result | TIMEOUT ❓ |
| Profit | $+0.00 |
| Duration Real | 60,521 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:04:39.426795 |
| SDK Status | ✅ OK |

### [A.2] Blitz — EURUSD-OTC — PUT
| Campo | Valor |
|-------|-------|
| Order ID | True |
| Asset | EURUSD-OTC |
| Type | binary |
| Direction | PUT |
| Amount | $1.00 |
| Duration | 60s |
| Open Price | N/A |
| Close Price | N/A |
| Result | TIMEOUT ❓ |
| Profit | $+0.00 |
| Duration Real | 33,975 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:05:41.138378 |
| SDK Status | ✅ OK |

### [A.3] Binary — EURUSD-OTC — CALL
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | EURUSD-OTC |
| Type | binary |
| Direction | CALL |
| Amount | $1.00 |
| Duration | 60s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:06:34.766642 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [A.4] Binary — EURUSD-OTC — PUT
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | EURUSD-OTC |
| Type | binary |
| Direction | PUT |
| Amount | $1.00 |
| Duration | 60s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:06:36.633437 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [A.5] Digital — BTCUSD — CALL
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | BTCUSD |
| Type | digital |
| Direction | CALL |
| Amount | $1.00 |
| Duration | 60s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:06:39.316153 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [A.6] Digital — BTCUSD — PUT
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | BTCUSD |
| Type | digital |
| Direction | PUT |
| Amount | $1.00 |
| Duration | 60s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:06:42.846254 |
| SDK Status | ❌ FAIL |
| Error Detail | SDK rejected digital buy: {'code': 'error_place_digital_order', 'message': 'invalid instrument'}... |

### [B.7] Forex — BTCUSD — BUY
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | BTCUSD |
| Type | forex |
| Direction | buy |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:06:46.131799 |
| SDK Status | ❌ FAIL |
| Error Detail | SDK rejected margin order: None... |

### [B.8] Forex — BTCUSD — SELL
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | BTCUSD |
| Type | forex |
| Direction | sell |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:07:17.183500 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [B.9] Stocks — MSFT — BUY
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | MSFT |
| Type | stock |
| Direction | buy |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:07:18.708816 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [B.10] Stocks — MSFT — SELL
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | MSFT |
| Type | stock |
| Direction | sell |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:07:19.798706 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [B.11] Crypto — BTCUSD — BUY
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | BTCUSD |
| Type | crypto |
| Direction | buy |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:07:21.114717 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [B.12] Crypto — BTCUSD — SELL
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | BTCUSD |
| Type | crypto |
| Direction | sell |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:07:22.841827 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [B.13] Commodity — Gold — BUY
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | Gold |
| Type | commodity |
| Direction | buy |
| Amount | $1.00 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:07:23.971818 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [B.14] Commodity — Gold — SELL
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | Gold |
| Type | commodity |
| Direction | sell |
| Amount | $1.00 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:07:25.151848 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [B.15] Index — US30 — BUY
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | US30 |
| Type | index |
| Direction | buy |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:07:26.955533 |
| SDK Status | ❌ FAIL |
| Error Detail | SDK rejected margin order: None... |

### [B.16] Index — US30 — SELL
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | US30 |
| Type | index |
| Direction | sell |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:07:58.634792 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [B.17] Etf — BTCUSD — BUY
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | BTCUSD |
| Type | etf |
| Direction | buy |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:08:00.383249 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

### [B.18] Etf — BTCUSD — SELL
| Campo | Valor |
|-------|-------|
| Order ID | 0 |
| Asset | BTCUSD |
| Type | etf |
| Direction | sell |
| Amount | $1.01 |
| Duration | 0s |
| Open Price | N/A |
| Close Price | N/A |
| Result | ERROR ❓ |
| Profit | $+0.00 |
| Duration Real | 0 ms |
| Signal Confidence | 0.00 |
| Timestamp | 2026-05-03T12:08:02.023292 |
| SDK Status | ❌ FAIL |
| Error Detail | Traceback (most recent call last):... |

## SECCIÓN 3: ANÁLISIS DE CALIDAD DE SEÑALES
| Activo | Señal Servidor | Direction Elegida | Resultado | ¿Señal Acertó? |
|--------|----------------|-------------------|-----------|----------------|
| EURUSD-OTC | NEUTRAL (Default to CALL) | CALL | TIMEOUT | ❌ No |
| EURUSD-OTC | NEUTRAL (Default to CALL) | PUT | TIMEOUT | ❌ No |
| EURUSD-OTC | NEUTRAL (Default to CALL) | CALL | ERROR | ❌ No |
| EURUSD-OTC | NEUTRAL (Default to CALL) | PUT | ERROR | ❌ No |
| BTCUSD | NEUTRAL (Default to CALL) | CALL | ERROR | ❌ No |
| BTCUSD | NEUTRAL (Default to CALL) | PUT | ERROR | ❌ No |

- **Precisión Señal Servidor:** 0.0% (0/6)

## SECCIÓN 4: ANÁLISIS DE MARGEN (Grupo B)
| Activo | Spread Real | Slippage | Leverage | PnL Realizado |
|--------|-------------|----------|----------|---------------|
| BTCUSD | 0.000000 | N/A | 1 | $+0.00 |
| BTCUSD | 0.000000 | N/A | 1 | $+0.00 |
| MSFT | 0.000000 | N/A | 1 | $+0.00 |
| MSFT | 0.000000 | N/A | 1 | $+0.00 |
| BTCUSD | 0.000000 | N/A | 1 | $+0.00 |
| BTCUSD | 0.000000 | N/A | 1 | $+0.00 |
| Gold | 0.000000 | N/A | 1 | $+0.00 |
| Gold | 0.000000 | N/A | 1 | $+0.00 |
| US30 | 0.000000 | N/A | 1 | $+0.00 |
| US30 | 0.000000 | N/A | 1 | $+0.00 |
| BTCUSD | 0.000000 | N/A | 1 | $+0.00 |
| BTCUSD | 0.000000 | N/A | 1 | $+0.00 |

## SECCIÓN 5: BUGS Y HALLAZGOS
**[BUG-LIVE-BINARY]**
- **Módulo:** binary
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 74, in place_binary_option
    success, order_id = self.api.buy(amount, asset, direction.lower(), duration_sec // 60)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 41, in buy
    self.api.buyv3(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_binary.py", line 30, in __call__
    self.send_websocket_request(self.name, data, str(request_id))
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\base.py", line 25, in send_websocket_request
    return self.api.send_websocket_request(name, msg,request_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\api.py", line 405, in send_websocket_request
    self.websocket.send(data)
  File "C:\Users\JCBV\AppData\Local\Programs\Python\Python311\Lib\site-packages\websocket\_app.py", line 186, in send
    raise WebSocketConnectionClosedException("Connection is already closed.")
websocket._exceptions.WebSocketConnectionClosedException: Connection is already closed.

- **Estado:** OPEN

**[BUG-LIVE-BINARY]**
- **Módulo:** binary
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 74, in place_binary_option
    success, order_id = self.api.buy(amount, asset, direction.lower(), duration_sec // 60)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 41, in buy
    self.api.buyv3(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_binary.py", line 25, in __call__
    "user_balance_id": int(self.api.balance_id)
                       ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-DIGITAL]**
- **Módulo:** digital
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 117, in place_digital_option
    success, order_id = self.api.buy_digital_spot(asset, amount, direction.lower(), duration_sec // 60)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 66, in buy_digital_spot
    return self.buy_digital_spot_v2(active, amount, action, duration)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 135, in buy_digital_spot_v2
    raise e
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 125, in buy_digital_spot_v2
    request_id = self.api.place_digital_option_v2(instrument_id, active_id, amount)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\api.py", line 870, in place_digital_option_v2
    "user_balance_id": int(self.balance_id)
                       ^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-DIGITAL]**
- **Módulo:** digital
- **Descripción:** SDK rejected digital buy: {'code': 'error_place_digital_order', 'message': 'invalid instrument'}
- **Estado:** OPEN

**[BUG-LIVE-FOREX]**
- **Módulo:** forex
- **Descripción:** SDK rejected margin order: None
- **Estado:** OPEN

**[BUG-LIVE-FOREX]**
- **Módulo:** forex
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-STOCKS]**
- **Módulo:** stock
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-STOCKS]**
- **Módulo:** stock
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-CRYPTO]**
- **Módulo:** crypto
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-CRYPTO]**
- **Módulo:** crypto
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-COMMODITY]**
- **Módulo:** commodity
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-COMMODITY]**
- **Módulo:** commodity
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-INDEX]**
- **Módulo:** index
- **Descripción:** SDK rejected margin order: None
- **Estado:** OPEN

**[BUG-LIVE-INDEX]**
- **Módulo:** index
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-ETF]**
- **Módulo:** etf
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

**[BUG-LIVE-ETF]**
- **Módulo:** etf
- **Descripción:** Traceback (most recent call last):
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\tests\live\helpers\trade_executor.py", line 161, in place_margin_order
    success, order_id = self.api.buy_order(
                        ^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\core\ratelimit.py", line 105, in wrapper
    return func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\mixins\orders_mixin.py", line 292, in buy_order
    self.api.buy_order(
  File "D:\Programacion\API-IQ\IQOP-API-JOHNBARZOLA\iqoptionapi\ws\channels\orders\buy_place_order_temp.py", line 43, in __call__
    "user_balance_id":int(self.api.balance_id),
                      ^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

- **Estado:** OPEN

## SECCIÓN 6: RENDIMIENTO Y LATENCIA
| Operación | Min (ms) | Max (ms) | Avg (ms) |
|-----------|----------|----------|----------|
| Trade Execution (blitz) | 33975 | 60521 | 47248 |

## SECCIÓN 8: VEREDICTO FINAL
| GRUPO | SUBCATEGORÍA | SDK STATUS | TRADING STATUS | VEREDICTO |
|-------|--------------|------------|----------------|-----------|
| A | Blitz | ✅ Sin errores | No ejecutado | ✅ READY |
| A | Binary | ❌ Errores detectados | No ejecutado | ❌ NOT READY |
| A | Digital | ❌ Errores detectados | No ejecutado | ❌ NOT READY |
| B | Forex | ❌ Errores detectados | No ejecutado | ❌ NOT READY |
| B | Stocks | ❌ Errores detectados | No ejecutado | ❌ NOT READY |
| B | Crypto | ❌ Errores detectados | No ejecutado | ❌ NOT READY |
| B | Commodity | ❌ Errores detectados | No ejecutado | ❌ NOT READY |
| B | Index | ❌ Errores detectados | No ejecutado | ❌ NOT READY |
| B | Etf | ❌ Errores detectados | No ejecutado | ❌ NOT READY |

### VEREDICTO GLOBAL: NOT READY ❌
- **SDK Error Rate:** 88.9%