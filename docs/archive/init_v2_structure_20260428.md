# init_v2 Structure Analysis — Sprint 4 TAREA 3
Date: 2026-04-28

## Top-Level Keys

The `initialization-data` (v2/v3) payload from IQ Option server contains:

```
{
  "binary":     { "actives": { "<id>": { ... } } },
  "turbo":      { "actives": { "<id>": { ... } } },
  "blitz":      { "actives": { "<id>": { ... } } },  // Optional, may not appear
  "currency":   "...",
  "is_buyback": true/false,
  "groups":     [ ... ]
}
```

## Key Finding: NO Margin/CFD Categories in init_v2

**CONFIRMED**: `init_v2` does **NOT** contain categories like `"forex"`, `"cfd"`, 
`"crypto"`, `"stocks"`, `"commodities"`, or `"indices"`.

Margin-type instruments are obtained **exclusively** via the WS message:
```json
{"name": "sendMessage", "msg": {"name": "get-instruments", "body": {"type": "forex"}}}
```

## Binary/Turbo Active Structure

Each active inside `binary.actives` or `turbo.actives`:

```json
{
  "name": "front.EURUSD",
  "description": "EUR/USD (OTC)",
  "ticker": "EURUSD-OTC",
  "enabled": true,
  "is_suspended": false,
  "id": 76,
  "group_id": 1,           // <-- Used by instruments.py to classify type
  "precision": 6,
  "schedule": [[start, end], ...],
  "option": {
    "profit": { "commission": 15 },
    "expiration_times": [60, 120, 300, ...]
  }
}
```

## Group ID Mapping (for classifying binary/turbo actives as margin types)

| group_id | Instrument Type |
|----------|----------------|
| 1        | forex          |
| 2        | stocks         |
| 3        | commodities    |
| 4        | indices        |
| 16       | crypto         |
| 41       | etf            |
| Other    | cfd            |

## How the SDK Gets Margin Instruments

1. **Primary**: `get_instruments("forex")` / `get_instruments("crypto")` etc. via WS
2. **Fallback**: `_extract_instruments_from_init()` classifies binary/turbo actives 
   by their `group_id` to synthesize instrument lists when WS returns empty

## Recommendation

The current `_extract_instruments_from_init()` correctly iterates over `"binary"` and 
`"turbo"` categories only — this is correct because those are the only categories 
containing structured active data with `group_id`. No changes needed.
