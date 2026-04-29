# Arquitectura del SDK (v8.9.995)

## Diagrama de Capas

```mermaid
graph TD
    User["Usuario / Robot"] -->|usa| Facade["stable_api.py (Fachada)<br/>IQ_Option — punto de entrada único"]
    
    subgraph Mixins ["Dominios (Mixins)"]
        Orders["OrdersMixin"]
        Positions["PositionsMixin"]
        Streams["StreamsMixin"]
        Management["ManagementMixin"]
    end
    
    Facade --> Orders
    Facade --> Positions
    Facade --> Streams
    Facade --> Management
    
    Orders --> Core["api.py (Core)"]
    Positions --> Core
    Streams --> Core
    Management --> Core
    
    subgraph Security ["Módulos de Seguridad / Stealth"]
        SubMgr["SubscriptionManager"]
        CB["CircuitBreaker"]
        RL["RateLimiter"]
        Scheduler["SessionScheduler"]
        IPRot["ip_rotation (Dev only)"]
    end
    
    Streams --> SubMgr
    Management --> CB
    Management --> Scheduler
    Orders --> RL
    Positions --> RL
    Core --> Session["http/session.py (Chrome 124 Headers)"]
```

## Módulos del SDK

| Módulo | Propósito | Entorno | Integrado en |
| :--- | :--- | :--- | :--- |
| `stable_api.py` | Fachada pública del SDK | Ambos | Punto de entrada |
| `api.py` | Motor WS/HTTP (protocolo base) | Ambos | `stable_api.py` |
| `mixins/orders_mixin` | Órdenes Binary/Digital/CFD | Ambos | `stable_api.py` |
| `mixins/positions_mixin` | Cierre y monitoreo de posiciones | Ambos | `stable_api.py` |
| `mixins/streams_mixin` | Suscripciones de mercado (velas) | Ambos | `stable_api.py` |
| `mixins/management_mixin` | Conexión, reconexión, metadata | Ambos | `stable_api.py` |
| `subscription_manager` | Límite de 15 streams simultáneos | Ambos | `streams_mixin` |
| `circuit_breaker` | Protección ante baneos/429/403 | Ambos | `management_mixin` |
| `session_scheduler` | Delays humanizados entre sesiones | Ambos | `management_mixin` |
| `ip_rotation` | Rotación IP vía WARP | Dev only | `connect_with_rotation` |
| `core/ratelimit.py` | Token bucket para ráfagas de órdenes | Ambos | `orders/positions` |
| `http/session.py` | Headers Chrome 124 y TLS | Ambos | `api.py` |
