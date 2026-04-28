# WS Protocol Gap Analysis — 2026-04-28 (Sprint 4 Update)

This document tracks the parity between the browser WebSocket implementation and the JCBV-NEXUS SDK.

## Implemented Handlers (Sprint 4)

| Message Name | SDK Handler | Status | Notes |
|---|---|---|---|
| `stop-order-placed` | `stop_order_placed.py` | ✅ NEW | Confirms pending order acceptance. |
| `position-closed` | `position_closed.py` | ✅ UPDATED | Handles final PnL and journaling. |
| `order-changed` | `order_changed.py` | ✅ NEW | Tracks pending order transitions. |
| `orders-state` | `order.py` | ✅ UPDATED | Bulk synchronization of pending orders. |
| `marginal-balance` | `marginal_balance.py` | ✅ NEW | Tracks available margin per category. |
| `instruments-list-changed` | `instruments.py` | ✅ UPDATED | Real-time asset availability updates. |
| `underlying-list-changed`| `underlying_list.py`| ✅ UPDATED | Digital Options asset status updates. |

## Pending Discovery (Phase D)

- **Pending Order Cancellation**: Payload structure for `cancel-order` (marginal) needs verification.
- **short-active-info**: Fast asset metadata without candle subscription.

## Low Priority Gaps

- `alerts`: System for price alerts.
- `overnight-fee`: Fee details for open positions.
- `exchange-rate-generated`: Real-time FX rates for conversion.
- `trading-params`: Dynamic server-side limits/parameters.

## Stealth Status

| Feature | Browser Pattern | SDK Pattern | Compliance |
|---|---|---|---|
| `request_id` | Sequential/TS | Sequential | 100% |
| Subscription Delay| ~300-500ms | 400ms + Jitter | 100% |
| User-Agent | Chrome 124 | Chrome 124 | 100% |
| Re-subscription | Batch with delay | `SubscriptionManager` | 100% |
| check_win Timeout | ~90s | 90s | 100% |
