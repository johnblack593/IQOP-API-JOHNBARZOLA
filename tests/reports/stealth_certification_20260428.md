# Stealth Certification Report: v9.0.0 Candidate (JCBV-NEXUS)

**Date**: 2026-04-28
**Status**: PASSED
**Version**: 8.9.999-stealth-ready -> 9.0.0

## 1. Objective
Ensure the JCBV-NEXUS SDK establishes WebSocket connections and requests data in a manner indistinguishable from a legitimate Chrome 124 browser session to prevent detection and silent asset-blocking (Rate Limits / 0 Margin Assets).

## 2. Hardening Measures Implemented

### 2.1. Authentication Parity (`authenticate` payload)
- **Problem**: The SDK was using the deprecated `ssid` endpoint, flagging the connection immediately as legacy/bot. The server no longer responds to this endpoint with a `profile` message.
- **Fix**: Replaced the `ssid` payload with the modern `authenticate` payload.
  ```json
  {"name": "authenticate", "msg": {"ssid": "...", "protocol": 3, "session_id": "", "client_session_id": ""}}
  ```
- **Result**: The server now responds with `authenticated`, aligning the SDK with current browser flows.

### 2.2. Humanized Initialization Delays
- **Problem**: The SDK historically requested all 6 instrument categories in parallel milliseconds after connection, immediately triggering rate limits and resulting in missing assets (0 margin assets loaded).
- **Fix**: 
  - Injected a `STEALTH_POST_AUTH_DELAY` (2.5s) to mimic frontend asset loading before initiating data queries.
  - Injected a `STEALTH_INSTRUMENT_REQUEST_DELAY` (1.5s) sequentially between category requests (`forex`, `cfd`, `crypto`, etc.) within `get_all_open_time()`.
- **Result**: Data requests are paced naturally. 100% of available assets are successfully loaded without silent rate-limits.

### 2.3. Active Keep-Alive (Heartbeat Loop)
- **Problem**: The SDK lacked an active `ping` loop. Browsers actively send pings every 5-10 seconds to maintain the WebSocket connection.
- **Fix**: Implemented a daemon thread `_start_heartbeat_loop` in `api.py` that sends a `ping` resource with an exact timestamp every `STEALTH_HEARTBEAT_INTERVAL` (5.0s) ± Jitter.
- **Result**: The connection is maintained actively from the client side, avoiding idle disconnects and masking bot signatures.

### 2.4. Profile Handling Refactor
- **Problem**: The old `ssid` endpoint automatically returned the `profile`. The new `authenticate` payload does not. The SDK would hang for 15s waiting for the profile.
- **Fix**: Explicitly send `core.get-profile` immediately after receiving the `authenticated` signal. Reduced the strict profile wait timeout to avoid blocking execution, as the connection is already proven successful.

## 3. Validation
The `stealth_stress_test.py` was executed, performing 120 rapid subscription/unsubscription cycles interspersed with full instrument refreshes. 

### Results:
- **Connection**: Success. No WARP proxy required.
- **Initialization**: Loaded 266 binary and 222 turbo assets.
- **Stability**: Maintained connection throughout the stress test without being banned or rate-limited.

**Verdict**: The Stealth Hardening phase is complete and successful. The SDK is ready for v9.0.0 release.
