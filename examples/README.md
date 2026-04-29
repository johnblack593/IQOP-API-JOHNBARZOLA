# Examples — JCBV-NEXUS SDK v9.1.000

Scripts de ejemplo para uso inmediato del SDK.
Todos requieren un archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

## Ejemplos Disponibles

| Script | Descripción |
|--------|-------------|
| 01_basic_connection.py | Conectar, verificar balance, desconectar |
| 02_buy_binary.py       | Comprar binary option y esperar resultado |
| 03_buy_digital.py      | Comprar digital option y esperar resultado |
| 04_candle_stream.py    | Stream de velas en tiempo real |
| 05_multiasset_robot.py | Robot multi-activo con SubscriptionManager |
| 06_research_blitz.py   | Investigación de activos tipo blitz/turbo |

## Ejecutar

```bash
python examples/01_basic_connection.py
python examples/02_buy_binary.py
```

> ⚠️ Usar siempre cuenta PRACTICE para pruebas.
