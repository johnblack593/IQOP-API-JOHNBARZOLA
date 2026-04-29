# Debug Tools — Internal Use Only

Scripts de diagnóstico manual para el SDK JCBV-NEXUS.
Requieren conexión real a IQ Option y credenciales en `.env`.
No son tests de pytest — no se ejecutan en CI.

| Script | Propósito |
|--------|-----------|
| debug_brute_force.py | Forzar conexión con reintentos |
| debug_dump_init.py | Volcar mensaje de inicialización WS |
| debug_events_map.py | Mapear eventos del dispatcher |
| debug_raw_payload.py | Inspeccionar payloads WS crudos |
| debug_reconnect.py | Simular reconexión y medir latencia |

Uso: `python tests/fixtures/debug-tools/<script>.py`
