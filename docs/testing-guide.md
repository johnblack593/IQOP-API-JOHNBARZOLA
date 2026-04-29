# Guía de Testing — JCBV-NEXUS SDK v9.1.000

Este SDK utiliza una suite de pruebas profesional basada en `pytest` para garantizar la estabilidad y el cumplimiento de las políticas de Stealth.

## Estructura de la Suite

```text
tests/
├── unit/             # Pruebas aisladas con mocks (sin red)
│   ├── core/         # Lógica central (Ratelimit, Expiration)
│   ├── stealth/      # Mecanismos anti-ban (Headers, CircuitBreaker)
│   ├── trading/      # Ejecución de órdenes y posiciones
│   └── regression/   # Prevención de bugs históricos
├── integration/      # Pruebas de flujo completo con red real
└── fixtures/         # Datos JSON y scripts de soporte (antes examples/)
```

## Ejecución de Tests

### Requisito previo
Instalar dependencias de desarrollo:
```bash
pip install pytest pytest-asyncio
```

### Ejecutar todos los tests unitarios
```bash
python -m pytest tests/unit/ -v --tb=short
```

### Ejecutar por dominio
```bash
# Solo stealth
python -m pytest tests/unit/stealth/ -v

# Solo trading
python -m pytest tests/unit/trading/ -v
```

### Ejecutar tests de integración
Requiere un archivo `.env` configurado con credenciales reales:
```bash
python -m pytest tests/integration/ -v
```

## Convenciones
1. **Nombres**: Los archivos deben comenzar con `test_` y describir el módulo, no el sprint (Ej: `test_orders.py` en lugar de `test_sprint3.py`).
2. **Fixtures**: Usar siempre el fixture `mock_iq` definido en `tests/unit/conftest.py` para asegurar consistencia en los mocks.
3. **Mantenimiento**: Cualquier bug corregido debe incluir un test en `tests/unit/regression/`.
