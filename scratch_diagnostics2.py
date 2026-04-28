import os, time, json
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
print("Conectando...")
ok, msg = api.connect()
if not ok:
    print('CONEXION FALLIDA:', msg)
    exit(1)

print('CONEXION EXITOSA')
api.change_balance('PRACTICE')
time.sleep(2)

print('\n=== PROBANDO TIPOS DE INSTRUMENTOS EXPLICITOS ===')
for itype in ['blitz','turbo','turbo-option','speed-option','sprint']:
    try:
        api.api.instruments = None
        api.api.send_websocket_request('sendMessage', {
            'name': 'get-instruments',
            'version': '3.0',
            'body': {'type': itype}
        })
        time.sleep(1.5)
        print(f'{itype}: enviado sin error')
        from iqoptionapi import global_value as gv
        data = getattr(api.api, 'instruments', {})
        count = len(data.get('instruments', [])) if isinstance(data, dict) else 0
        print(f'{itype}: {count} activos en ws dict')
    except Exception as e:
        print(f'{itype}: ERROR {e}')

print('\n=== PROBANDO TIPOS DE MARGEN ===')
margin_types = ['forex','stocks','crypto','commodities','indices','etf','cfd','margin','leverage']
for itype in margin_types:
    try:
        api.api.instruments = None
        api.api.send_websocket_request('sendMessage', {
            'name': 'get-instruments',
            'version': '3.0',
            'body': {'type': itype}
        })
        time.sleep(1.5)
        data = getattr(api.api, 'instruments', {})
        count = len(data.get('instruments', [])) if isinstance(data, dict) else 0
        print(f'{itype:20s}: {count} activos en dict')
    except Exception as e:
        print(f'{itype:20s}: ERROR {e}')

print('\n=== TURBO VS BINARY EXPIRATIONS ===')
# Solo vemos init data
init_v2 = api.get_all_init_v2()
for cat in ['turbo','binary', 'blitz']:
    if init_v2 and cat in init_v2:
        actives = init_v2[cat].get('actives', {})
        print(f'{cat}: {len(actives)} activos')
        if actives:
            sample_key = list(actives.keys())[0]
            print(f'  Ejemplo: {actives[sample_key].get("name")} expirations: {actives[sample_key].get("expirations", [])[:3]}')

api.close()
