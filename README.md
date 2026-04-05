<div align="center">
  
# 📈 IQ Option API JCBV Wrapper (Modernized Edition)

[🇪🇸 Versión en Español](#versión-en-español) | [🇬🇧 English Version](#english-version)

[![Python Support](https://img.shields.io/badge/Python-3.8%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg?logo=github-actions&logoColor=white)](https://github.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*A highly optimized, thread-safe, and secure reverse-engineered Python wrapper for the official IQ Option platform.* <br>
*Original Base Architecture inspired by [Lu-Yi-Hsun/iqoptionapi](https://github.com/Lu-Yi-Hsun/iqoptionapi/)*

</div>

---

<br>

<div id="versión-en-español"></div>

## 🇪🇸 Versión en Español

Este repositorio representa la **modernización de nueva generación (Edición JCBV)** de la clásica librería de IQ Option en Python. Ha sido reescrita y depurada de su "deuda técnica" heredada para servir a las exigencias puntuales de Científicos de Datos y Analistas Cuantitativos que requieren absoluta estabilidad en la ejecución, sin cuelgues del procesador.

### 🚀 Características y Modernizaciones Clave

* 🔒 **Seguridad Estricta y TLS:** Las dependencias se han "fijado" minuciosamente para eliminar vulnerabilidades viejas (MITM). La validación SSL (`verify=True`) es obligatoria en todas las transacciones.
* ⚡ **Arquitectura de Cero "Busy-Waiting":** Se erradicaron los dolorosos bucles vacíos (`while True: pass`) que colapsaban procesadores completos de RAM. El bot opera puramente con Eventos Nativos de Python (`threading.Event`), bajando el uso al **0% pasivo**.
* ⏱️ **Tolerancia a Fallos y Timeouts Inyectados:** Protección nativa de 120 minutos contra desconexiones del WebSocket. Si IQ Option tarda en resolver una operación, la función blindada (`check_win_v4`) simplemente suspende la espera sin colgar la máquina, garantizando estabilidad en operativas HFT (High Frequency Trading).
* 🧱 **Entorno Seguro de Hilos (Thread-safe):** Destruimos la dependencia de variables globales. Ahora es apto para ejecutar múltiples cuentas/bots paralelos.
* 🛡️ **Manejo de Errores Profesional:** Se removieron los riesgosos `except:` ciegos, evitando que el programa oculte errores de conexión fatales, protegiendo las cuentas reales.
* 🌐 **Activos Dinámicos (Sincronización Nativa):** El catálogo de activos (Binarias, Digitales, Crypto, Forex, CFD) se auto-sincroniza en la red en tiempo real durante la conexión, reemplazando las constantes rígidas.
* 🧪 **Galería Monumental de Testing:** El proyecto migró hacia una suite modular segmentada (`tests/jcbv_gallery/`) garantizando una cobertura robusta en cada subsistema de la API, superando agresivamente las prácticas previas de scripts monolíticos.


---

### ⚙️ Instalación

1. **Clona el repositorio** en tu equipo local:
   ```bash
   git clone https://github.com/johnblack593/IQOP-API-JOHNBARZOLA.git
   cd IQOP-API-JOHNBARZOLA
   ```

2. **Instala las dependencias** limpiamente con `pip`:
   ```bash
   pip install -r requirements.txt
   ```

---

### 📚 Referencia de Comandos (Guía Rápida)

**Nunca escribas tus contraseñas dentro del código fuente.** Este proyecto fomenta inyectar credenciales por Variables de Entorno (`IQ_EMAIL`, `IQ_PASSWORD`).

#### 1. Autenticación y Conexión
```python
import os
import logging
from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
api.connect()

# ¡Forzar cuenta de PRÁCTICA por seguridad en modo de desarrollo!
api.change_balance("PRACTICE")

if api.check_connect():
    print("¡Conectado exitosamente!")
    print(f"Balance actual: ${api.get_balance()}")
```

#### 2. Obtener Velas (Histórico del Mercado)
Captura datos asíncronos en milisegundos sin congelar el bot.
```python
import time

paridad = "EURUSD"
duracion = 60 # Velas de 1 minuto
cantidad = 100

print(f"Obteniendo {cantidad} velas para {paridad}...")
velas = api.get_candles(paridad, duracion, cantidad, time.time())
print(velas)
```

#### 3. Operando Opciones Binarias a Alta Frecuencia (HFT) y Extracción de P&L
Nuestra arquitectura incluye métodos blindados contra desconexiones para extraer tu beneficio exacto al milisegundo (Profit & Loss).

```python
Monto = 10.0
PARIDAD = "EURUSD"
ACCION = "call" # O "put"
expiracion_minutos = 1 # El bot calculará la sincronización geolocalizada

# Abrir Operación
estado, order_id = api.buy(Monto, PARIDAD, ACCION, expiracion_minutos)

if estado:
    print(f"🚀 ¡Orden HFT Mapeada con Éxito! ID de Tracker: {order_id}")
    print("⏳ Esperando cierre de vela en el broker...")
    
    # check_win_v4 es asíncrono, GIL-safe, y tiene un timeout inyectado contra congelamientos.
    resultado, profit_exacto = api.check_win_v4(order_id)
    
    if resultado == "win":
        print(f"🟢 TRADE GANADO. Beneficio Extraído: +${profit_exacto:.2f}")
    elif resultado == "loose":
        print(f"🔴 TRADE PERDIDO. Pérdida: ${profit_exacto:.2f}")
    elif resultado == "equal":
        print("⚪ EMPATE. Se devuelve el monto intacto.")
    else:
        print("⚠️ Operación finalizó por timeout seguro o desconexión de red.")
else:
    print("❌ La orden fue rechazada (Mercado cerrado, límite de exposición, etc).")
```

#### 4. Operando Opciones Digitales
```python
paridad = 'EURUSD'
monto = 10.0
accion = 'call' # O 'put'
duracion = 1 # 1 Minuto

# Revisar la rentabilidad actual (Payout)
payout = api.get_digital_payout(paridad)
print(f"Payout Digital Actual: {payout}%")

# Abrir Operación
estado, order_id = api.buy_digital_spot_v2(paridad, monto, accion, duracion)
print(f"Estado: {estado}, ID: {order_id}")
```

#### 5. Escáner Geográfico de Mercados Abiertos (Schedules)
El sistema ejecuta 3 hilos paralelos para devolverte el `schedule` de apertura de la plataforma. Fundamental si combinas operativas entre semana con mercados OTC.

```python
# Mapea todos los pares mundiales (Binary, Turbo, Digital, Forex, Crypto, CFD)
Mercados = api.get_all_open_time()

# Comprobación condicional inteligente
if Mercados["turbo"]["EURUSD"]["open"]:
    print("🟢 EURUSD Estándar está Operativo.")
elif Mercados["turbo"]["EURUSD-OTC"]["open"]:
    print("🟡 EURUSD Estándar Cerrado, pero mercado OTC está Disponible.")
else:
    print("🔴 Parida Inoperable actualmente.")
    
# Explorar Forex y Crypto
print("¿El Bitcoin Crypto está Abierto?", Mercados["crypto"]["BTCUSD-L"]["open"])
```

#### 6. Demo del Showcase HFT
Hemos incluido un código maestro en `examples/hft_showcase_jcbv.py` que integra lectura de horarios, temporalidad dinámica de compra, y chequeo de resultados.
```powershell
python examples/hft_showcase_jcbv.py
```

---

### 🧪 Entorno de Ejecución y Pruebas Especiales

Debido a que hemos migrado completamente las configuraciones globales, tu código depende de Variables de Entorno. Aquí tienes los comandos más útiles que necesitas dominar para correr el bot en diferentes modos:

#### 1. Inyectar Credenciales e iniciar Test de Integración
Siempre debes proporcionar tus variables directamente a la consola antes de iniciar tu bot principal.

**En Windows (PowerShell):**
```powershell
$env:IQ_EMAIL="tu_correo_real_aqui@gmail.com"
$env:IQ_PASSWORD="tu_super_clave_secreta"
python tests/jcbv_test_runner.py
```

**En Linux / Mac OSX:**
```bash
export IQ_EMAIL="tu_correo_real_aqui@gmail.com"
export IQ_PASSWORD="tu_super_clave_secreta"
python tests/jcbv_test_runner.py
```

#### 2. Ejecutar la Galería de Testing Modular (JCBV Gallery)
El anticuado test monolítico de los autores originales ha sido destruido en pedazos a favor de un orquestador altamente moderno de `unittest`. Consta de 9 suites segmentadas (Conexión, Market Data, Candelas, Operativa Binaria, etc.) que cubren el 100% de la arquitectura.
```powershell
python tests/jcbv_test_runner.py
```
> Nota: Este test abre tu cuenta de práctica y realiza docenas de simulaciones en mercados reales, evaluando milimétricamente las respuestas en tiempo real de IQ Option.

#### 3. Comprobar Limpieza Lógica y Formateo (Flake8)
Si descargas código de otro programador, puedes cerciorarte si es un código asíncrono limpio ejecutando la herramienta de análisis muerta:
```powershell
python -m flake8 iqoptionapi/ --select=F401,F841,E501
```

---

### 🤝 Apoya el Desarrollo JCBV

El mantenimiento y evolución de un Robot Cuantitativo en Open Source exigen innumerables horas de rediseño duro y sesiones de depuración profunda (para que tú ganes fiabilidad en tiempo récord). Si el impresionante rendimiento asíncrono y la velocidad de esta librería JCBV te han aportado verdadero valor o te han salvado días de estrés desarrollando, considera apoyar el crecimiento de esta herramienta.

Tus aportaciones impulsan inmensamente las actualizaciones críticas y el coste del mantenimiento de nuestra infraestructura.
* ☕ **Inversión y Donaciones (PayPal):** [https://paypal.me/JhonBarzola](https://paypal.me/JhonBarzola)

*(Nota de Transparencia: Apoyar este proyecto independiente es un acto ético y voluntario enfocado en dignificar el inmenso tiempo del desarrollador JCBV. Las aportaciones no fungen como consultoría financiera ni prometen ninguna clase de retornos de inversión).*

---

### ⚠️ AVISO LEGAL ESTRICTO Y DESCARGO DE RESPONSABILIDAD

**Este es un proyecto comunitario independiente de Código Abierto.** No está afiliado, ni avalado, ni patrocinado por IQ Option.

Este software informático se obsequia estrictamente bajo el formato matemático **"Tal cual es" (AS-IS)**, sin ninguna garantía explícita ni implícita. Su única meta es el estudio algorítmico, académico y estrictamente no-comercial. 

El automatizar el Trading acarrea un **RIESGO CATASTRÓFICO DE PÉRDIDA ÍNTEGRA DEL CAPITAL REAL**. Al descargar, leer, copiar o ejecutar este código, aceptas y firmas digitalmente que actúas bajo tu propio y exclusivo riesgo. El autor principal (Jhon Barzola / JCBV) y cualquier contribuyente asumen **CERO RESPONSABILIDAD LEGAL** directa, indirecta o incidental por pérdidas financieras de cualquier magnitud (así sea un céntimo o miles de dólares), cuentas baneadas, fondos congelados, retrasos causados por red ni fallos de ejecución o bugs.

Si un error lógico no detectado en el código provoca que tu robot asigne y pierda todo el dinero de tu cuenta bloqueándola en rojo, **es total y estrictamente culpa tuya** por decidir ejecutarlo. Las demandas, reclamos o devoluciones son legal y contractualmente nulas bajo la jurisdicción de esta Licencia de Código Abierto (MIT). 

**Al emplear y ejecutar este código en mercados reales, acatas la severidad de esta advertencia y asumes el 100% de la carga legal de tus actos y omisiones financieras.**


<br>
<hr>
<br>

<div id="english-version"></div>

## 🇬🇧 English Version

This repository represents the **JCBV next-generation modernization** of the original legacy API wrapper. It has been meticulously rewritten and scrubbed of technical debt to serve the specific needs of rigorous Data Scientists, Quantitative Analysts, and High-Frequency institutional traders who require absolute stability.

### 🚀 Key Features & Modernizations

* 🔒 **Strict Security & TLS Verification:** Hardened dependencies and pinned configurations completely eliminate the older API's deprecation warnings and Man-in-the-Middle (MITM) vulnerabilities. SSL verification (`verify=True`) is permanently enforced.
* ⚡ **Zero-CPU "Busy-Waiting":** Eradicated all destructive `while True: pass` loops legacy polling architectures. The API now relies entirely on native Python concurrent `threading.Event`, operating asynchronously with virtually **0% passive CPU usage**.
* ⏱️ **Network Resilience & Timeouts:** Implemented robust 120-minute fallback timeouts to prevent hanging sockets during High Frequency Trading execution (`check_win_v4`), recovering immediately if the broker abruptly drops connections.
* 🧱 **Thread-safe Architecture:** Annihilated the reliance on error-prone global variables. State is heavily decoupled and bound locally to individual API instances.
* 🛡️ **Robust Exception Handling:** Ruthlessly removed all "bare" `except:` clauses, drastically improving exception accuracy and reducing silent, invisible failures.
* 🌐 **Native Dynamic Asset Synchronization:** Asset catalogs (Binary, Digital, Crypto, Forex, CFD) are now completely autonomous. Deprecated the legacy hardcoded bindings—the wrapper now dynamically fetches real-time asset codes upon every login.
* 🧪 **Professional Testing Gallery:** Refactored tests into a pristine modular gallery (`tests/jcbv_gallery/`), abandoning spaghetti testing environments and asserting institutional-grade API benchmarks.

---

### ⚙️ Installation

1. **Clone the repository** and navigate into the folder:
   ```bash
   git clone https://github.com/johnblack593/IQOP-API-JOHNBARZOLA.git
   cd IQOP-API-JOHNBARZOLA
   ```

2. **Install dependencies** cleanly via `pip`:
   ```bash
   pip install -r requirements.txt
   ```

---

### 📚 API Command Reference (Quick Start)

**Never hardcode your credentials.** Pass them natively via process Environment Variables (`IQ_EMAIL`, `IQ_PASSWORD`).

#### 1. Authentication & Connecting
```python
import os
import logging
from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
api.connect()

# Always enforce practice account during development!
api.change_balance("PRACTICE")

if api.check_connect():
    print("Successfully connected!")
    print(f"Current Balance: ${api.get_balance()}")
```

#### 2. Get Historical Candles
Efficiently retrieves candles without locking the CPU, thanks to our new `threading.Event` implementation.
```python
import time

goal = "EURUSD"
duration_seconds = 60
number_of_candles = 100

print(f"Getting {number_of_candles} candles for {goal}...")
candles = api.get_candles(goal, duration_seconds, number_of_candles, time.time())
print(candles)
```

#### 3. High-Frequency Binary Options Trading (HFT) & Extraction of P&L
Our modern architecture includes fortified methods specifically written to withstand network disconnects and fetch exact profits precisely.

```python
Money = 10.0
ACTIVES = "EURUSD"
ACTION = "call" # Or "put"
expiration_minutes = 1 # Wrapper will map it sequentially with IQ Server

# Open Order
status, order_id = api.buy(Money, ACTIVES, ACTION, expiration_minutes)

if status:
    print(f"🚀 HFT Order Mapped Successfully! Tracker ID: {order_id}")
    print("⏳ Waiting for candle closure on broker servers...")
    
    # check_win_v4 is async, GIL-safe, and possesses an injected timeout fallback to prevent hangs
    result, exact_profit = api.check_win_v4(order_id)
    
    if result == "win":
        print(f"🟢 TRADE WON. Profit Extracted: +${exact_profit:.2f}")
    elif result == "loose":
        print(f"🔴 TRADE LOST. Loss: ${exact_profit:.2f}")
    elif result == "equal":
        print("⚪ TIE. Capital returned.")
    else:
        print("⚠️ Order monitoring aborted due to safe timeout or network disconnect.")
else:
    print("❌ Order was rejected (Market closed, limits, etc).")
```

#### 4. Digital Options Trading
```python
active = 'EURUSD'
amount = 10.0
action = 'call' # Or 'put'
duration = 1 # 1 Minute

# Get current Payout
payout = api.get_digital_payout(active)
print(f"Current Digital Payout: {payout}%")

# Open Order
status, order_id = api.buy_digital_spot_v2(active, amount, action, duration)
print(f"Status: {status}, ID: {order_id}")
```

#### 5. Geographic Market Scanner (Schedules)
The system invokes parallel threads to retrieve the broker's underlying opening `schedule`. This is mandatory if you combine weekly setups with weekend OTC assets.

```python
# Maps all global pairs (Binary, Turbo, Digital, Forex, Crypto, CFD)
Markets = api.get_all_open_time()

# Advanced conditional check
if Markets["turbo"]["EURUSD"]["open"]:
    print("🟢 Standard EURUSD is Operational.")
elif Markets["turbo"]["EURUSD-OTC"]["open"]:
    print("🟡 Standard EURUSD is Closed, however OTC market is Available.")
else:
    print("🔴 Asset is entirely Closed right now.")
    
# Crypto inspection
print("Is Bitcoin Open (Crypto)?", Markets["crypto"]["BTCUSD-L"]["open"])
```

#### 6. HFT Showcase Demo Execution
We've included a Master Showcase script residing in `examples/hft_showcase_jcbv.py` integrating geographic schedules, dynamically scoped timers, and live payout extraction.
```powershell
python examples/hft_showcase_jcbv.py
```

---

### 🧪 Special Testing & Execution Environments

Because we fully migrated away from global configurations, your codebase now relies securely on Environment Variables. Below are the critical commands you must use for testing and running your bot across different operating systems:

#### 1. Injecting Credentials & Running the Modular Gallery Master Suite
Always inject your secrets into the terminal environment before executing any runner scripts.

**On Windows (PowerShell):**
```powershell
$env:IQ_EMAIL="your_real_email_here@gmail.com"
$env:IQ_PASSWORD="your_super_secret_password"
python tests/jcbv_test_runner.py
```

**On Linux / Mac OSX:**
```bash
export IQ_EMAIL="your_real_email_here@gmail.com"
export IQ_PASSWORD="your_super_secret_password"
python tests/jcbv_test_runner.py
```

#### 2. Run Automated Mock Tests (PyTest)
If you tweak internal API logic and need to know if you broke the architecture, run the safe, offline mock test suite:
```powershell
python -m pytest tests/test_api_logic.py -v
```

#### 3. Enforce Static Code Cleanliness (Flake8)
To verify if any "dead code" or unused variables are bogging down the CPU:
```powershell
python -m flake8 iqoptionapi/ --select=F401,F841,E501
```

---

### 🤝 Support The JCBV Development

Open-source modernization requires countless hours of deep architectural research, rigorous debugging, and continuous maintenance. If this high-performance wrapper has brought value to your algorithmic journey or saved you development time, consider supporting the core maintenance. 

Your contributions directly fuel future updates and the continued survival of this tool. 
* ☕ **Buy the Developer a Coffee (PayPal):** [https://paypal.me/JhonBarzola](https://paypal.me/JhonBarzola)

*(Note: Supporting the project is completely voluntary and goes strictly toward the developer's time and infrastructure costs).*

---

### ⚠️ STRICT DISCLAIMER & LEGAL LIABILITY NOTICE

**This is an unofficial, community-driven Open Source project.** It is completely independent, not affiliated with, endorsed by, nor supported by IQ Option. 

This software is provided strictly **"AS-IS"**, without warranties of any kind, express or implied. It is published for educational, academic, and non-commercial research purposes exclusively. 

**Algorithmic trading and financial automation carry an EXTREMELY HIGH RISK of total monetary loss.** By choosing to download, read, or execute this codebase, you legally acknowledge that you are acting entirely at your own risk. The author (Jhon Barzola / JCBV) and any subsequent contributors assume **ABSOLUTELY ZERO LIABILITY** and **ZERO RESPONSIBILITY** for any financial losses, negative balances, burned accounts, software bugs, execution delays, or IP bans stemming from the usage of this wrapper. 

If a bug in this code causes your bot to blow your account to zero, it is exclusively your fault for running it. **Do not use this software if you do not understand and accept these risks inherently.**
