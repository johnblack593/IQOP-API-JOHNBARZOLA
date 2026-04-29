# API Reference — JCBV-NEXUS SDK v9.0.000

Este documento detalla los métodos públicos disponibles en la clase principal `IQ_Option`.

## Conexión y Sesión
| Método | Descripción | Retorno |
| :--- | :--- | :--- |
| `connect()` | Inicia la sesión HTTP y la conexión WebSocket. | `(bool, str)` |
| `check_connect()` | Verifica si el WebSocket está actualmente conectado. | `bool` |
| `disconnect()` | Cierra todas las conexiones y libera recursos. | `None` |
| `change_balance(balance_mode)` | Cambia entre cuenta REAL y PRACTICE. | `None` |

## Trading — Binary Options
| Método | Descripción | Retorno |
| :--- | :--- | :--- |
| `buy(amount, active, action, expirations)` | Compra una opción binaria/turbo. | `(bool, int)` |
| `sell_option(option_id)` | Venta temprana de una opción abierta. | `(bool, dict)` |
| `check_win(order_id, timeout)` | Espera el resultado de una operación. | `str` o `None` |

## Trading — Digital Options
| Método | Descripción | Retorno |
| :--- | :--- | :--- |
| `buy_digital_spot(active, amount, action, duration)` | Compra una opción digital. | `(bool, int)` |
| `sell_digital_option(id)` | Venta temprana de opción digital. | `(bool, str)` |
| `check_win_digital(order_id, timeout)` | Espera el resultado de una digital. | `str` o `None` |

## Trading — CFD / Forex / Stocks
| Método | Descripción | Retorno |
| :--- | :--- | :--- |
| `buy_order(instrument_type, active, direction, amount, leverage, ...)` | Abre una posición con apalancamiento. | `(bool, int)` |
| `close_position(position_id)` | Cierra una posición abierta. | `(bool, dict)` |
| `get_open_positions(instrument_type)` | Obtiene posiciones actuales. | `(bool, dict)` |

## Market Data (Streams)
| Método | Descripción | Retorno |
| :--- | :--- | :--- |
| `subscribe_candles(active, size)` | Se suscribe a actualizaciones de velas. | `None` |
| `unsubscribe_candles(active, size)` | Cancela la suscripción a velas. | `None` |
| `get_candles(active, size, count, end_time)` | Obtiene historial de velas (bloqueante). | `list` |

## Información de Cuenta
| Método | Descripción | Retorno |
| :--- | :--- | :--- |
| `get_balance()` | Retorna el balance actual de la cuenta activa. | `float` |
| `get_currency()` | Retorna el símbolo de la moneda de la cuenta. | `str` |
| `get_profile()` | Retorna el perfil completo del usuario. | `dict` |
