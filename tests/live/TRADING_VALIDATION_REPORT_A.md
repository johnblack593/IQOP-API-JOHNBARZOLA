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

### VEREDICTO GLOBAL: NOT READY ❌
- **SDK Error Rate:** 66.7%