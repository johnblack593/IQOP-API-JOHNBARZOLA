# Margin Trading Protocol — Reverse Engineered from Chrome 124 Browser Session

**Date**: 2026-04-28
**Source**: Chrome DevTools MCP + WebSocket Interceptor on iqoption.com/traderoom
**Account**: Demo (user_id: 123456789)

---

## 1. OPEN MARGIN POSITION (Market Order)

### 1.1 Message Name Pattern
The browser uses **category-specific** message names:
- `marginal-forex.place-market-order` — for Forex pairs (e.g., EURUSD)
- `marginal-cfd.place-market-order` — for CFD/Stocks (e.g., AAPL)
- `marginal-crypto.place-market-order` — for Crypto (e.g., BTCUSD)

> **IMPORTANT**: This is NOT the legacy `place-order-temp` (v4.0). The browser uses the
> modern `marginal-{type}.place-market-order` (v1.0).

### 1.2 Exact Payload Captured
```json
{
  "name": "sendMessage",
  "request_id": "150",
  "local_time": 191577,
  "msg": {
    "name": "marginal-forex.place-market-order",
    "version": "1.0",
    "body": {
      "side": "buy",
      "user_balance_id": 987654321,
      "instrument_id": "mf.1",
      "instrument_active_id": 1,
      "leverage": "1000",
      "margin": "10",
      "is_margin_isolated": true,
      "take_profit": {
        "type": "pnl",
        "value": "5"
      },
      "stop_loss": {
        "type": "pnl",
        "value": "-3"
      },
      "keep_position_open": false
    }
  }
}
```

### 1.3 Field Documentation

| Field | Type | Description |
|---|---|---|
| `side` | string | `"buy"` or `"sell"` |
| `user_balance_id` | int | Balance ID (demo or real) |
| `instrument_id` | string | Instrument ID prefix: `mf.{active_id}` (forex), `mc.{active_id}` (cfd), `mcy.{active_id}` (crypto) |
| `instrument_active_id` | int | Numeric active ID (e.g., 1 for EURUSD) |
| `leverage` | string | Leverage as string (e.g., `"1000"` for x1000) |
| `margin` | string | Amount in USD as string (e.g., `"10"`) |
| `is_margin_isolated` | bool | Always `true` from browser |
| `take_profit` | object/null | `{"type": "pnl", "value": "5"}` or null |
| `stop_loss` | object/null | `{"type": "pnl", "value": "-3"}` or null |
| `keep_position_open` | bool | Whether to keep position open past session |

### 1.4 TP/SL Types
- `"pnl"` — P&L amount in account currency (e.g., `"5"` = +$5 profit)
- `"price"` — Absolute asset price (e.g., `"1.17200"`)
- `"percent"` — Percentage of margin (e.g., `"50"` = 50%)

> **Note**: `stop_loss.value` is NEGATIVE for PnL type (e.g., `"-3"` = -$3 loss)

### 1.5 Instrument ID Format
```
marginal-forex  -> instrument_id = "mf.{active_id}"
marginal-cfd    -> instrument_id = "mc.{active_id}"
marginal-crypto -> instrument_id = "mcy.{active_id}"
```

---

## 2. CLOSE MARGIN POSITION

### 2.1 From existing SDK code (already implemented)
```json
{
  "name": "sendMessage",
  "msg": {
    "name": "close-position",
    "version": "1.0",
    "body": {
      "position_id": "af30128248b29624bc8f2bd7f67b8920"
    }
  }
}
```

> The position_id is a hex string (MD5-like hash), not a numeric ID.

---

## 3. SUBSCRIBE TO POSITION UPDATES

### 3.1 Exact payload
```json
{
  "name": "subscribeMessage",
  "msg": {
    "name": "positions-state"
  }
}
```

### 3.2 Subscribe to specific position
```json
{
  "name": "sendMessage",
  "msg": {
    "name": "subscribe-positions",
    "version": "1.0",
    "body": {
      "frequency": "frequent",
      "ids": ["af30128248b29624bc8f2bd7f67b8920"]
    }
  }
}
```

---

## 4. GET OPEN POSITIONS (Portfolio)

### 4.1 Get all open positions by instrument type
```json
{
  "name": "sendMessage",
  "msg": {
    "name": "portfolio.get-positions",
    "version": "3.0",
    "body": {
      "user_id": 123456789,
      "user_balance_id": 987654321,
      "instrument_types": ["marginal-forex"],
      "offset": 0,
      "limit": 30
    }
  }
}
```

### 4.2 Instrument types for margin
- `"marginal-forex"` — Forex margin positions
- `"marginal-cfd"` — CFD/Stocks margin positions
- `"marginal-crypto"` — Crypto margin positions

---

## 5. GET AVAILABLE LEVERAGES

### 5.1 Trading group params request
```json
{
  "name": "sendMessage",
  "msg": {
    "name": "trading-settings.get-trading-group-params",
    "version": "1.0",
    "body": {
      "instrument_type": "marginal-forex"
    }
  }
}
```

This returns leverage options, max margin, min margin, etc., grouped by active_id.

---

## 6. OVERNIGHT FEE QUERY

### 6.1 Get overnight fee for instrument
```json
{
  "name": "sendMessage",
  "msg": {
    "name": "marginal-forex-instruments.get-overnight-fee",
    "version": "1.0",
    "body": {
      "instrument_type": "marginal-forex",
      "active_id": 1
    }
  }
}
```

---

## 7. MODIFY TP/SL (Existing in SDK)

### 7.1 Change TPSL
Already implemented via `change-tpsl` (version 2.0) in `change_tpsl.py`.

---

## 8. POSITION STATE SUBSCRIPTION

### 8.1 Get marginal balance
```json
{
  "name": "sendMessage",
  "msg": {
    "name": "marginal-portfolio.get-marginal-balance",
    "version": "1.0",
    "body": {
      "user_balance_id": 987654321
    }
  }
}
```

### 8.2 Subscribe balance changes
```json
{
  "name": "sendMessage",
  "msg": {
    "name": "marginal-portfolio.subscribe-balance-changed",
    "version": "1.0",
    "body": {
      "user_balance_id": 987654321
    }
  }
}
```

---

## 9. KEY DIFFERENCES FROM LEGACY SDK

| Aspect | Legacy SDK (`place-order-temp`) | Browser (Modern) |
|---|---|---|
| Message name | `place-order-temp` | `marginal-{type}.place-market-order` |
| Version | `4.0` | `1.0` |
| Amount field | `amount` (float) | `margin` (string) |
| Leverage field | `leverage` (int) | `leverage` (string) |
| TP/SL format | `stop_lose_kind`/`stop_lose_value` | `stop_loss: {type, value}` |
| Instrument ID | `instrument_id` (string name) | `instrument_id` (prefix format) + `instrument_active_id` |
| Margin type | Not specified | `is_margin_isolated: true` |
| Keep open | Not specified | `keep_position_open: false` |
