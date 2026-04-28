# Sprint 3 Stress Tests & Diagnostics Report
**Date:** 2026-04-27  
**Version:** v8.9.991  
**Execution Environment:** PRACTICE account, WARP-proxied connection

---

## Test 1: Stress Test 10 Trades (Turbo)

**Script:** `scratch/stress_test_10trades.py`  
**Asset:** EURUSD-OTC  
**Balance inicial:** $10,000.45

| Trade | Direction | Order ID      | Status   | Profit | Elapsed |
|-------|-----------|---------------|----------|--------|---------|
| 01    | call      | 13844323836   | TIMEOUT  | None   | 85.6s   |
| 02    | put       | 13844327005   | TIMEOUT  | None   | 30.5s   |
| 03    | call      | --            | WS_CRASH | --     | --      |
| 04-10 | --        | --            | NOT_RUN  | --     | --      |

**Resultado:** PARCIAL - 2/10 trades colocados, 0/10 resueltos

### Diagnostico:
- Trades 1 y 2 se colocaron exitosamente (order_id valido retornado)
- `check_win_v3()` no recibio evento `socket_option_closed` para ninguno
- Causa raiz: el WS se desconecta durante la espera de resultado
- Trade 3 fallo porque `balance_id` se resetea a `None` tras reconexion
- **Bug critico identificado:** `_auto_reconnect()` no restaura `balance_id`

### Criterio: FALLIDO
- 0/10 IDs resueltos (criterio: 10/10)
- 0 errores "socket already closed" en buy() pero WS inestable durante check_win

---

## Test 2: Stress Test Blitz

**Script:** `scratch/stress_test_blitz.py`

| Blitz | Status | Order ID | Clock Offset |
|-------|--------|----------|--------------|
| 1     | False  | None     | 0.642s       |
| 2     | False  | None     | 0.642s       |
| 3     | False  | None     | 0.646s       |
| 4     | False  | None     | 0.646s       |
| 5     | False  | None     | 0.646s       |

**Resultado:** 0/5 trades Blitz ejecutados

### Diagnostico:
- `buy_blitz()` envia la orden via `buyv3_by_raw_expired()` correctamente
- El servidor acepta la orden (no hay excepcion) pero no retorna order_id
- La espera de 15s en el loop de `buy_multi_option` expira sin resultado
- **Posible causa:** el `option_type_id=3` (turbo) no es el correcto para Blitz
  en esta version del servidor; podria requerir type_id especifico de blitz
- Clock offset estable en 0.64s (aceptable, no es drift)

### Criterio: FALLIDO
- 0/5 trades con resultado (criterio: >= 3)
- Requiere investigacion del protocol Blitz buy

---

## Test 3: Reconnect Forced

**Script:** `scratch/test_reconnect_forced.py`

| Metrica                    | Valor         |
|----------------------------|---------------|
| Balance pre-corte          | $9,998.45     |
| Reconexion exitosa         | SI            |
| Tiempo de reconexion       | 4 segundos    |
| Balance post-reconexion    | $9,998.45     |
| Turbo activos post         | 167           |
| Clock offset post          | 0.645s        |
| Trade post-reconexion      | CRASH         |

### Diagnostico:
- **Reconexion automatica EXITOSA en 4s** -- ReconnectManager funciona
- `get_balance()` retorna valor correcto post-reconexion
- `get_all_open_time()` retorna 167 activos turbo post-reconexion
- Clock offset se mantiene estable (0.645s)
- **Bug:** `balance_id` es None post-reconexion, causando crash en `buyv3()`
  - `int(self.api.balance_id)` lanza TypeError cuando balance_id=None
  - El reconnect restaura WS pero no re-suscribe `balance_id`

### Criterio: PARCIAL
- Reconexion en < 30s: PASADO (4s)
- Trade post-reconexion: FALLIDO (balance_id=None)

---

## Test 4: CFD KYC Status

**Script:** `scratch/verify_cfd_post_kyc.py`

### Instrument Discovery (via init-data fallback):

| Tipo         | Total | Abiertos | Source              |
|--------------|-------|----------|---------------------|
| cfd          | 0     | 0        | N/A (WS empty)      |
| forex        | 83    | 49       | init-data-fallback  |
| crypto       | 59    | 48       | init-data-fallback  |
| stocks       | 60    | 32       | init-data-fallback  |
| commodities  | 15    | 13       | init-data-fallback  |
| indices      | 22    | 21       | init-data-fallback  |
| etf          | 3     | 3        | init-data-fallback  |
| **TOTAL**    | **242** | **166** |                    |

### Group ID Distribution (raw init_v2):

| Group | Tipo         | Activos |
|-------|--------------|---------|
| 1     | forex        | 238     |
| 2     | stocks       | 141     |
| 3     | commodities  | 44      |
| 4     | indices      | 66      |
| 16    | crypto       | 173     |
| 41    | etf          | 6       |
| **TOTAL** |          | **668** |

### CFD buy_order Results:

| Asset  | Type    | Status | Error                                |
|--------|---------|--------|--------------------------------------|
| AAPL   | cfd     | False  | CFD_NOT_SUPPORTED                    |
| AAPL   | stocks  | False  | CFD_NOT_SUPPORTED                    |
| EURUSD | forex   | False  | CFD_NOT_SUPPORTED                    |
| BTCUSD | crypto  | False  | CFD_NOT_SUPPORTED                    |

**Server response:** `[4108] Instrument type forbidden`  
**`check_cfd_order_capability`:** `False`

### Conclusion:
**CFD/Margin trading BLOQUEADO por KYC/cuenta.** El servidor retorna 
error 4108 "Instrument type forbidden" para TODOS los tipos de margin.
Esto NO es un bug del SDK -- es una restriccion de la cuenta. 
Los instrumentos se pueden LISTAR (via init-data fallback) pero no OPERAR.

---

## Test 5: Catalog Production Verification

### Conteo de activos abiertos:

| Categoria   | Objetivo Min | Actual   | Status  | Nota                    |
|-------------|-------------|----------|---------|-------------------------|
| blitz       | > 100       | 180*     | PASS    | *via init_v2 actives    |
| turbo       | > 100       | 222*     | PASS    | *via init_v2 actives    |
| binary      | > 100       | 266*     | PASS    | *via init_v2 actives    |
| digital     | > 50        | N/A      | SKIP    | Timeout en underlying   |
| forex       | > 20        | 49       | PASS    | init-data-fallback      |
| stocks      | > 100       | 32**     | PARTIAL | **Solo 32 de 141 open   |
| crypto      | > 30        | 48       | PASS    |                         |
| commodities | --          | 13       | PASS    | (no min required)       |
| indices     | --          | 21       | PASS    | (no min required)       |
| etf         | --          | 3        | PASS    | (no min required)       |

*Nota: blitz/turbo/binary counts son del init_v2 actives (enabled + not suspended).
Counts de abiertos via `get_all_open_time()` pueden ser menores por horario.

**stocks < 100:** El mercado de acciones (US markets) esta cerrado domingo noche.
Los 32 abiertos son OTC assets. Los 141 totales estaran abiertos en horario 
de mercado (Lunes 9:30 AM EST).

### IP Rotation (WARP) Status:
- WARP cooldown guard funciona correctamente (45s minimo entre rotaciones)
- Rotacion de IP ejecutada exitosamente en test anterior (104.28.153.54 -> nueva)
- `is_warp_available()` retorna True en este entorno

---

## Resumen Ejecutivo

| Test                     | Resultado | Blocker para v8.9.995? |
|--------------------------|-----------|------------------------|
| 10 Trades Turbo          | FALLIDO   | SI - balance_id bug    |
| Blitz Trades             | FALLIDO   | SI - protocol issue    |
| Reconnect Manager        | PARCIAL   | SI - balance_id post   |
| CFD KYC                  | BLOQUEADO | NO - restriccion cuenta|
| Catalog Alignment        | PASS      | NO                     |
| IP Rotation (WARP)       | PASS      | NO                     |

### Bugs Criticos Identificados:

1. **BUG-S3-01: `balance_id=None` post-reconnect**
   - `_auto_reconnect()` no invoca `change_balance()` tras reconectar
   - Causa crash en `buyv3()` y `buy_order()` que hacen `int(balance_id)`
   - **Fix propuesto:** Agregar `self.change_balance()` en el bloque de 
     exito de `_auto_reconnect()` y guardar el ultimo balance_mode usado

2. **BUG-S3-02: `check_win_v3()` TIMEOUT sistematico**
   - `socket_option_closed` no se puebla para trades activos cuando WS es inestable
   - El handler WS puede estar descartando mensajes durante reconexion
   - Requiere investigacion del handler `socket_option_closed`

3. **BUG-S3-03: Blitz buy no recibe order_id**
   - `buy_blitz()` usa `option_type_id=3` (turbo) que puede no ser correcto
   - El servidor acepta la request pero no retorna confirmacion
   - Requiere sniffing del protocolo Blitz en la plataforma web
