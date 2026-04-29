# JCBV-NEXUS IQ Option API SDK (v9.1.000)

**IQ Option API con esteroides para robots de trading.**

API wrapper de IQ Option diseñada para sistemas de trading algorítmico que requieren control absoluto del protocolo, resiliencia ante fallos y mecanismos avanzados de evasión de detección (Stealth).

---

## ¿Qué es esto?
Este SDK es una evolución del wrapper estándar, optimizado para:
1. **Baja Latencia**: Gestión eficiente de hilos y WebSocket.
2. **Alta Disponibilidad**: Reconexión inteligente y gestión de sesiones.
3. **Seguridad (Stealth)**: Emulación de comportamiento humano y fingerprint de browser real.

## Características Principales
- **Conexión Stealth**: Emulación de Chrome 124 (Headers, Jitter, Fingerprinting).
- **Arquitectura Modular**: Lógica dividida en Mixins (Orders, Positions, Streams, Management).
- **Gestión de Streams**: `SubscriptionManager` que limita y humaniza las peticiones de datos.
- **Protección de Capital**: `CircuitBreaker` integrado para detener el bot ante anomalías o pérdidas excesivas.
- **Inteligencia de Mercado**: Motores de calidad de mercado, patrones de velas y régimen de mercado.

## Instalación
```bash
git clone https://github.com/johnblack593/IQOP-API-JOHNBARZOLA.git
cd IQOP-API-JOHNBARZOLA
pip install -e .
cp .env.example .env   # Completar con credenciales reales
```

## Ejemplos de Uso
La carpeta `examples/` contiene scripts listos para usar:
- `01_basic_connection.py`: Conexión y balance.
- `02_buy_binary.py`: Compra de opciones binarias.
- `03_buy_digital.py`: Compra de opciones digitales.
- `05_multiasset_robot.py`: Ejemplo de robot multi-activo.

## Inicio Rápido (Quick Start)
```python
from iqoptionapi.stable_api import IQ_Option
import os

iq = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
check, reason = iq.connect()

if check:
    print("Conexión exitosa")
    iq.change_balance("PRACTICE")
    # Comprar $1 en EURUSD a 1 minuto
    iq.buy(1, "EURUSD", "call", 1)
else:
    print(f"Error: {reason}")
```

## Configuración (.env)
Ver [.env.example](.env.example) para todas las variables disponibles.

## Arquitectura del SDK
El SDK utiliza un patrón de **Fachada** (`IQ_Option`) que hereda de múltiples **Mixins** especializados. 
Para más detalles, ver [docs/architecture.md](docs/architecture.md).

## Notas de Seguridad (Stealth / Anti-ban)
Ver [docs/stealth-guide.md](docs/stealth-guide.md) para la guía completa.

## Guía de Desarrollo
1. Las nuevas funcionalidades de trading deben ir en `iqoptionapi/mixins/`.
2. Todo cambio debe ser validado con `pytest tests/unit/`.
3. Ver [docs/testing-guide.md](docs/testing-guide.md) para más info.

## Changelog
Ver [CHANGELOG.md](CHANGELOG.md) para el historial completo.
