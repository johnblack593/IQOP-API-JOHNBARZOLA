import json, re, os

# Intentar cargar desde la ruta especificada
target_file = "scratch/captured_digital_frame.json"

if not os.path.exists(target_file):
    print(f"Error: No se encontro el archivo '{target_file}'.")
    print("Instrucciones para el usuario:")
    print("  1. Abrir Chrome/Edge -> F12 -> Network -> WS")
    print("  2. Ir a iqoption.com y ejecutar UNA compra Digital minima ($1)")
    print("     en EURUSD-OTC, cualquier duracion")
    print("  3. En el panel WS, buscar el frame enviado que contiene")
    print("     'place-digital-option' o 'digital-options.place-digital-option'")
    print("  4. Copiar el JSON de ese frame y guardarlo en: scratch/captured_digital_frame.json")
    exit(1)

with open(target_file) as f:
    frame = json.load(f)

print("=== ESTRUCTURA DEL FRAME DIGITAL ===")
print(json.dumps(frame, indent=2))

# El frame puede ser el objeto completo o solo el contenido de 'msg'
msg = frame.get("msg", frame)
instrument_id = msg.get("instrument_id", msg.get("instrumentId", "?"))
print(f"\ninstrument_id raw: {instrument_id}")

# Parsear el formato: do{ID}A{TIME}...
# Ejemplo esperado: do76A100PT5M1 o do76PT5MSPTSPT
pattern = r'do(\d+)([A-Z]\w*)'
match = re.match(pattern, str(instrument_id))
if match:
    numeric_id = match.group(1)
    suffix = match.group(2)
    print(f"  -> Numeric ID: {numeric_id}")
    print(f"  -> Suffix: {suffix}")
    print(f"  -> Este ID deberia coincidir con ACTIVES.get('EURUSD-OTC') o similar")
else:
    print("  -> Formato no reconocido, guardar para analisis manual")
