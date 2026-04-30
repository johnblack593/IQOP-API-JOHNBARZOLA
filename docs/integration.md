# IQ Option SDK — Integration Guide (JCBV-NEXUS)

This document defines the public contract of the IQ Option SDK. All integrations with JCBV-NEXUS must adhere to these signatures and behaviors.

## Core API Methods

### 1. Connection Management
```python
def connect(self) -> bool:
```
- **Behavior**: Initializes HTTP session and WebSocket connection. Performs authentication.
- **Returns**: `True` if connected and authenticated, `False` otherwise.
- **Timeout**: Internal timeout of 30s for authentication.

---

### 2. Asset Discovery
```python
def get_all_open_time(self) -> dict:
```
- **Returns**: A complex nested dictionary containing open/close times for all asset types (`binary`, `turbo`, `digital`, etc.).
- **Nexus Usage**: Use this to filter active symbols before attempting trades.

---

### 3. Binary Trading (Binary/Turbo)
```python
def buy(self, amount: float, asset: str, action: str, expiration: int) -> tuple[bool, int | None]:
```
- **Arguments**:
  - `amount`: Investment amount (min 1.0).
  - `asset`: Symbol name (e.g., `"EURUSD"`, `"EURUSD-OTC"`).
  - `action`: `"call"` or `"put"`.
  - `expiration`: Expiration time in minutes (1, 2, 3, 4, 5).
- **Returns**: `(success, order_id)`.
  - `success`: `True` if the order was accepted by the server.
  - `order_id`: The server-side ID for tracking results. `None` if `success` is `False`.
- **Note**: This method is **thread-safe** and **rate-limited** (internal bucket).

```python
def check_win(self, order_id: int, timeout: float = 120.0) -> float | None:
```
- **Returns**: 
  - `float`: Profit/Loss amount (positive for win, negative for loss).
  - `None`: If timeout reached before result.

---

### 4. Digital Trading
```python
def buy_digital_spot(self, asset: str, amount: float, action: str, duration: int) -> tuple[bool, int | None]:
```
- **Arguments**: `duration` is 1, 5, or 15 minutes.
- **Returns**: `(success, order_id)`.

```python
def check_win_digital(self, order_id: int, timeout: float = 120.0) -> float | None:
```
- **Returns**: Same as `check_win`.

---

## Error Handling & Resiliency

- **Timeouts**: Methods like `buy()` and `check_win()` have internal reactive timeouts. They will NOT block indefinitely.
- **KILL-SWITCH**: If the WebSocket connection is lost, the SDK automatically **signals all pending events** to unblock waiting threads. This means `check_win()` may return `None` immediately if a disconnection occurs during the wait.
- **Auto-Reconnect**: The SDK handles reconnection automatically with exponential backoff.
- **Recommendation for Nexus**: 
    - Always check `iq.api.check_websocket_if_connect == 1` before initiating a trade.
    - Catch `websocket.WebSocketConnectionClosedException` in your trade logic to handle edge cases where the socket drops exactly during a `send()`.
- **Correlation**: Binary trades use a request-aware correlation engine. Multiple concurrent `buy()` calls are supported.
- **Memory Management**: The SDK automatically cleans up event stores and correlation queues after each trade or on failure.
- **Connectivity**: Cloudflare WARP is recommended for production environments to avoid IP blocks.

## Concurrency Limits
- **Safe Limit**: Up to 10 concurrent trade requests per second (internal rate limiter enforced).
- **Tracking**: Nexus should maintain its own local database mapping `order_id` to its internal strategy signals.
