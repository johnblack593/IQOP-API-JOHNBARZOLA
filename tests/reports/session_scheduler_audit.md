# Session Scheduler Audit

**Date:** 2026-04-27
**Target File:** `iqoptionapi/session_scheduler.py`

## Answers to Audit Questions

**1. ¿Qué hace exactamente?**
Calcula en base al tiempo UTC actual si los mercados de divisas (Sydney, Tokyo, London, New York) están abiertos o solapados. Determina si el bot tiene permitido operar (`is_trading_time`) bloqueando los fines de semana (basado en el cierre del viernes a las 22:00 UTC y apertura del domingo a las 22:00 UTC) y filtrando `blocked_hours_utc`. También sugiere los mejores activos para la sesión activa.

**2. ¿Tiene conflicto con el Connection Guard de la suite?**
**No.** `SessionScheduler` es puramente sincrónico, evaluando reglas estáticas en base al reloj del sistema (`datetime.now(timezone.utc)`). No crea hilos, no intercepta sockets, y no pausa la ejecución. Por tanto, es 100% seguro de usar en paralelo con Connection Guard.

**3. ¿Usa algún threading.Event o Lock que pueda colisionar con los stores de _wait_result?**
**No.** El código está libre de primitivas de concurrencia (`threading.Event`, `Lock`, `Condition`). Toda su lógica se basa en el paso de variables por valor, haciendo imposible que colisione o bloquee a `_wait_result`.

**4. ¿Debería integrarse con ReconnectManager?**
**Sí, de forma indirecta.** Si bien no necesita interactuar directamente con la capa WS, el bot o el script principal debería utilizar `is_trading_time()` para determinar si vale la pena mantener la conexión activa. Si `MarketSession.CLOSED` está activo (ej. Sábado al mediodía), `ReconnectManager` podría suspender los intentos de reconexión y apagar el socket voluntariamente para ahorrar memoria y CPU, y despertar automáticamente cuando la próxima ventana se abra.
