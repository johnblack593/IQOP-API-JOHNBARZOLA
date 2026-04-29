# CFD KYC Status Report
**Date:** 2026-04-27  
**Version:** v8.9.991

## Status: BLOQUEADO POR CUENTA

### Server Error
```
[4108] Instrument type forbidden
```

### Evidence
- `check_cfd_order_capability()` returns `False`
- `buy_order()` returns `CFD_NOT_SUPPORTED` for ALL margin types
- Server message: `Failed on command execution [4108] Instrument type forbidden`
- Tested with assets: AAPL (stocks), EURUSD (forex), BTCUSD (crypto)
- Tested with instrument_types: cfd, stocks, forex, crypto

### Instrument Discovery Works
The SDK correctly LISTS margin instruments via init-data fallback:
- forex: 83 instruments (49 open)
- crypto: 59 instruments (48 open)
- stocks: 60 instruments (32 open - weekend)
- commodities: 15 instruments (13 open)
- indices: 22 instruments (21 open)
- etf: 3 instruments (3 open)

### Root Cause
This is a **server-side account restriction**, NOT an SDK bug.
The PRACTICE account does not have CFD/Margin trading enabled.
Possible reasons:
1. KYC verification not fully completed
2. Account tier does not include margin trading
3. Regional restriction on margin products

### Recommendation
- Verify KYC status in IQ Option account settings
- Contact IQ Option support to enable margin trading on practice account
- This blocker does NOT affect Binary/Turbo/Digital/Blitz trading paths
