# WS Endpoints Catalog (Margin Assets)

Based on the WebSocket payload interception of the IQ Option Traderoom using Chrome DevTools MCP, we discovered the following endpoints that handle margin assets:

## Observed `marginal-*` Endpoints

1. **Crypto**:
   - `marginal-crypto-instruments.get-instruments-list`
   - `marginal-crypto-instruments.get-underlying-list`
   - `marginal-crypto-instruments.get-overnight-fee`
   - `marginal-crypto-instruments.instruments-list-changed`
   - `marginal-crypto-instruments.overnight-fee-changed`
   - `marginal-crypto-instruments.underlying-list-changed`
   - `marginal-crypto.order-modified`

2. **Forex**:
   - `marginal-forex-instruments.get-instruments-list`
   - `marginal-forex-instruments.get-underlying-list`
   - `marginal-forex-instruments.get-overnight-fee`
   - `marginal-forex-instruments.instruments-list-changed`
   - `marginal-forex-instruments.overnight-fee-changed`
   - `marginal-forex-instruments.underlying-list-changed`
   - `marginal-forex.order-modified`

3. **CFD (Contracts for Difference)**:
   There are NO endpoints named `marginal-stocks`, `marginal-indices`, `marginal-commodities`, or `marginal-etf`. Instead, we observed these specific identifiers inside the `marginal-cfd` payloads:
   - `marginal-cfd|Commodity`
   - `marginal-cfd|ETF`
   - `marginal-cfd|Index`
   - `marginal-cfd|Stock`

## Conclusion

The browser **DOES NOT** use separate `get-underlying-list` endpoints for stocks, indices, commodities, and ETFs. All these sub-categories are delivered together under the `marginal-cfd-instruments.get-underlying-list` endpoint. 

Therefore, in the SDK's `Get_instruments` routing logic, any requests for `stocks`, `indices`, `commodities`, or `etf` should be mapped to the `marginal-cfd-instruments` endpoint.
