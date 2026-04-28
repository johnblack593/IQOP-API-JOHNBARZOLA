# WS Protocol Gap Analysis — 2026-04-28 (Sprint 6 Update)

This document tracks the parity between the browser WebSocket implementation and the JCBV-NEXUS SDK.

## Implemented Handlers (Sprint 6)

| Message Name | SDK Handler | Method | Status | Notes |
|---|---|---|---|---|
| `stop-order-placed` | `stop_order_placed.py` | `place_stop_order` | ✅ PS5 | Confirms pending order acceptance. |
| `position-closed` | `position_closed.py` | `check_win_v3/v4` | ✅ PS5 | Handles final PnL and journaling. |
| `order-changed` | `order_changed.py` | `get_async_order` | ✅ PS5 | Tracks pending order transitions. |
| `orders-state` | `order.py` | `sync_state_on_connect` | ✅ PS5 | Bulk synchronization of pending orders. |
| `marginal-balance` | `marginal_balance.py` | `get_marginal_balance` | ✅ PS5 | Tracks available margin per category. |
| `alerts` | `alerts.py` | — | ✅ PS6 | Price alert notification handler (Reactive Class). |
| `overnight-fee` | `overnight_fee.py` | `overnight_fee_data` | ✅ PS6 | Fee details for open positions. |
| `short-active-info` | `short_active_info.py` | `get_short_active_info`| ✅ PS6 | Fast asset metadata without candle subscription. |
| `exchange-rate-generated`| `exchange_rate.py` | `get_exchange_rate` | ✅ PS6 | Real-time FX rates for conversion. |
| `trading-params` | `trading_params.py` | `get_payout` | ✅ PS6 | Dynamic server-side limits/parameters. |
| `instruments-list-changed` | `instruments.py` | — | ✅ PS4 | Real-time asset availability updates. |
| `underlying-list-changed`| `underlying_list.py`| — | ✅ PS5 | Digital Options asset status updates. |

## Stealth Status

| Feature | Browser Pattern | SDK Pattern | Compliance |
|---|---|---|---|
| `request_id` | Sequential/TS | Sequential | 100% |
| Subscription Delay| ~300-500ms | 400ms + Jitter | 100% |
| User-Agent | Chrome 147 | Chrome 147 | 100% |
| Re-subscription | Batch with delay | `SubscriptionManager` | 100% |
| Token Refresh | Every 4-24h | `_start_token_refresh_worker` | 100% |

## Next Steps
- Implement `place_pending_order` wrapper for `stop-order-placed`.
- Monitor `trading-params` for automatic risk adjustments.
