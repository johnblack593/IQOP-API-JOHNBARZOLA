# IQOP-API-JOHNBARZOLA (JCBV-NEXUS SDK)

**IQ Option API con esteroides para robots de trading — v8.9.999-PS7**

API wrapper de IQ Option con capa de inteligencia de mercado integrada.
Diseñada para sistemas como JCBV-NEXUS que requieren control absoluto
del protocolo y datos enriquecidos en tiempo real.

---

## Características principales

### Core (Sprint 7 Hardening)
- **Conexión WebSocket Stealth**: Headers Chrome 147, request_id secuencial y reconexión con Exponential Backoff + Jitter.
- **Session Hardening**: Background token refresh worker (cada 4h) para evitar expiración de sesión.
- **Operaciones Completas**: Digital, Binary, Turbo, Blitz, CFD/Forex con `place_stop_order`.
- **Portfolio Avanzado**: `get_open_positions(realtime_pnl=True)`, `create_price_alert()`, `get_position_history()`.
- **Resiliencia**: Rate limiting, idempotencia y circuit breaker integrados.

### Inteligencia de mercado (valor agregado)
| Módulo | Qué hace | Método principal |
|--------|----------|-----------------|
| `market_quality` | Detecta activos con spread anormal | `is_tradeable(asset, size)` |
| `pattern_engine` | 6 patrones de velas japonesas | `detect(asset, size)` |
| `market_regime` | Trending vs Ranging (ADX) | `get_regime(asset, size)` |
| `correlation_engine` | Correlación Pearson inter-activos | `get_correlation(a, b, size)` |
| `asset_scanner` | Top activos por payout + calidad | `get_best_payout_assets()` |
| `performance` | Win rate, EV, profit factor | `get_asset_score(asset, tf)` |

## Instalación

```bash
git clone https://github.com/johnblack593/IQOP-API-JOHNBARZOLA.git
cd IQOP-API-JOHNBARZOLA
pip install -e .
cp .env.example .env   # completar con credenciales reales
```

## Uso de Nuevas Funciones (Sprint 7)

### Real-time PnL & Positions
```python
# Obtener posiciones con PnL actualizado dinámicamente desde WS
positions = iq.get_open_positions(instrument_type="forex", realtime_pnl=True)
for pos in positions:
    print(f"ID: {pos['id']} PnL: {pos['pnl_estimate']}$")
```

### Alertas de Precio
```python
# Crear una alerta cuando el precio suba por encima de 1.0850
check, alert_id = iq.create_price_alert("EURUSD", 1.0850, "above")
```

### Historial de Trades
```python
# Obtener los últimos 50 trades de Digital Options
history = iq.get_position_history(instrument_type="digital-option", limit=50)
```

## Módulos disponibles

Todos accesibles como atributos de la instancia `IQ_Option`:

```python
iq.candle_cache          # Buffer de velas con deque(maxlen)
iq.trade_journal         # Historial de operaciones en sesión
iq.circuit_breaker       # Pausa automática ante rachas perdedoras
iq.martingale_guard      # Control de tamaño de posición
iq.validator             # Validación de parámetros antes de operar
iq.performance           # Métricas de rendimiento por activo
iq.market_quality        # Calidad de mercado en tiempo real
iq.pattern_engine        # Detección de patrones de velas
iq.market_regime         # Detección de tendencia/rango
iq.correlation_engine    # Correlación entre activos
iq.asset_scanner         # Scanner de mejores activos
```

## Testing

```bash
# Test de integración completo (Demo)
python scratch/test_full_flow.py

# Verificar cumplimiento de Stealth
python scratch/test_stealth_verify.py
```

## CI/CD

Jobs: `lint` (ruff) · `test` (pytest unit)
