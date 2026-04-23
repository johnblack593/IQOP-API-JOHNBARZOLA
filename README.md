# IQOP-API-JOHNBARZOLA

**IQ Option API con esteroides para robots de trading**

API wrapper de IQ Option con capa de inteligencia de mercado integrada.
Diseñada para sistemas como JCBV-NEXUS que requieren control absoluto
del protocolo y datos enriquecidos en tiempo real.

## Características principales

### Core
- Conexión WebSocket estable con reconexión automática y backoff
- Operaciones: Digital, Binary, Turbo, Blitz, CFD/Forex
- Portfolio: `get_open_positions()`, `get_order_status()`, `reconcile_missed_results()`
- Rate limiting, idempotencia y circuit breaker integrados

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

## Uso básico

```python
from iqoptionapi.stable_api import IQ_Option
import os

iq = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
check, reason = iq.connect()

if check:
  iq.change_balance("PRACTICE")

  # ¿Qué activos puedo operar ahora con mejor calidad?
  assets = iq.asset_scanner.get_best_payout_assets(
      instrument_type="turbo-option",
      top_n=3,
      min_payout=0.80
  )
  for a in assets:
      print(f"{a['asset']}: payout={a['payout']:.0%} regime={a['regime']}")

  # ¿Está EURUSD-OTC en tendencia o rango?
  regime = iq.market_regime.get_regime(1, 60)  # active_id=1, 1 minuto
  direction = iq.market_regime.get_trend_direction(1, 60)
  print(f"Régimen: {regime}, Dirección: {direction}")

  # Operar si el activo tiene buena calidad
  if iq.market_quality.is_tradeable(1, 60):
      status, order_id = iq.buy_digital_spot("EURUSD-OTC", 1.0, "call", 5)
      if status:
          result = iq.check_win_digital(order_id)
          print(f"Resultado: {result}")
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

## Reglas del protocolo (críticas)

- `"loose"` es el typo oficial del servidor IQ Option — nunca corregir
- Blitz instruments solo via `initialization-data` — nunca llamar `get_instruments("blitz")`
- `instrument_strike_value` viene en x1,000,000 — siempre dividir por `1e6`

## Testing

```bash
pip install -r requirements-dev.txt
python -m pytest tests/unit/ -v
```

## CI/CD

Jobs: `lint` (ruff) · `test` (pytest unit)
