# Guía de Stealth / Anti-ban

## El Problema
IQ Option emplea algoritmos avanzados para detectar comportamiento automatizado (bots). Las detecciones suelen basarse en:
1. **Fingerprint inconsistente**: Diferencia entre los headers del WebSocket y los de HTTP.
2. **Frecuencia de suscripción**: Suscribirse a demasiados activos simultáneamente (comportamiento no humano).
3. **Reconexiones agresivas**: Intentar conectar repetidamente tras un fallo sin tiempos de espera variables.

## Solución 1 — Fingerprint de Navegador
El SDK emula un entorno **Chrome 124** completo en `http/session.py`. 
- Se inyectan los mismos headers (`User-Agent`, `Origin`, `sec-ch-ua`) tanto en peticiones HTTP como en el handshake inicial del WebSocket.
- Se utiliza el perfil de idioma `es-419` (Latinoamérica) para mayor coherencia en la región del usuario.

## Solución 2 — Límite de Suscripciones
El `SubscriptionManager` impone un límite estricto de **15 suscripciones simultáneas** de velas. 
- Este número replica el límite observado en la aplicación web oficial.
- El gestor encola las peticiones y las procesa con un delay aleatorio (jitter) para evitar ráfagas sintéticas.

## Solución 3 — Reconexión con Jitter
La reconexión utiliza una estrategia de **Exponential Backoff** con ruido aleatorio:
- `base_delay * (2 ^ attempt) + random.uniform(-1.5, 1.5)`
- Esto evita que el servidor detecte un patrón de reconexión fijo y predecible.

## Solución 4 — Circuit Breaker
El `CircuitBreaker` actúa como un fusible de seguridad:
- **OPEN**: Si se detectan baneos temporales (403), rate limits (429) o pérdidas consecutivas, el circuito se abre y bloquea toda operación por 5 minutos.
- **HALF-OPEN**: Tras el tiempo de espera, permite un intento de prueba.
- **CLOSED**: Operación normal.

## Solución 5 — ip_rotation.py (SOLO DESARROLLO)
Para entornos de desarrollo propensos a baneos por pruebas constantes:
- Requiere Cloudflare WARP instalado.
- Se activa con `ENABLE_IP_ROTATION=true`.
- Rota la IP automáticamente cuando detecta señales de baneo de IQ Option.
- **ADVERTENCIA**: No usar en producción (servidores Linux) para evitar fallos por dependencias de sistema ausentes.

## Checklist de Producción
- [ ] `ENABLE_IP_ROTATION=false` (o ausente en entorno).
- [ ] `MAX_CONCURRENT_SUBSCRIPTIONS ≤ 15`.
- [ ] User-Agent == Chrome 124 (verificar `session.py`).
- [ ] `CircuitBreaker` activo y monitoreado.
- [ ] Logs configurados para alertar ante errores 429/403.
