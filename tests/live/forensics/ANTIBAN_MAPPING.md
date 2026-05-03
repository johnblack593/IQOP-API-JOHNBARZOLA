# JCBV-NEXUS SDK — Forensic Anti-Ban Mapping

## Browser Session Profile
- **User-Agent**: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36`
- **Client Hints**:
  - `sec-ch-ua`: `"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"`
  - `sec-ch-ua-mobile`: `?0`
  - `sec-ch-ua-platform`: `"Windows"`

## Network Flow (Auth)
1. **AppInit**: `GET https://iqoption.com/api/appinit`
   - Returns features and basic config.
2. **Session Check**: `GET https://auth.iqoption.com/api/v4/check-session`
   - Returns `ssid` and `user_id`.
   - **Cookie used**: `ssid`, `identity`.

## WebSocket Handshake
- **URL**: `wss://ws.iqoption.com/echo/websocket`
- **Headers observed**:
  - `Origin`: `https://iqoption.com`
  - `User-Agent`: (as above)
  - `Sec-WebSocket-Extensions`: `permessage-deflate; client_max_window_bits`
- **Backend Infrastructure**: `ws04.ws.prod.sc-ams-1b.quadcode.tech`

## Sequence Triggers (Opcode 8)
- Disconnect occurs if `send_ssid` is not sent within ~1 second of connection.
- Disconnect occurs if TLS JA3 signature doesn't match the reported Chrome 147 version.

## Key Cookies for Stealth
- `ssid`
- `identity`
- `device_id` (captured: `yCoEpoKfJW5i0dbe14A7`)
- `_ga`, `_scid` (Standard tracking cookies, should be simulated if possible).
