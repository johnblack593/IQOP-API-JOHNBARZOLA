import os, time, json
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
import logging

logging.basicConfig(level=logging.WARNING)

load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
ok, msg = api.connect()
if not ok:
    print('CONEXION FALLIDA:', msg)
    exit(1)

print('CONEXION EXITOSA')
api.change_balance('PRACTICE')
time.sleep(3)
ot = api.get_all_open_time()

print('=== CATEGORIAS DISPONIBLES EN SDK ===')
for cat, assets in ot.items():
    open_list = [k for k,v in assets.items() if v.get('open')]
    print(f'{cat.upper():20s}: {len(assets):4d} total | {len(open_list):4d} abiertos')

print('\n=== DETALLE CFD (primeros 20) ===')
cfd = ot.get('cfd', {})
for k,v in list(cfd.items())[:20]:
    # open key
    op = v.get(chr(111)+chr(112)+chr(101)+chr(110))
    print(f'  {k:30s} open={op}')

print('\n=== PROBANDO TIPOS DE INSTRUMENTOS EXPLICITOS ===')
for itype in ['blitz','turbo','turbo-option','speed-option','sprint']:
    try:
        api.api.send_websocket_request('sendMessage', {
            'name': 'get-instruments',
            'version': '3.0',
            'body': {'type': itype}
        })
        time.sleep(1.5)
        print(f'{itype}: enviado sin error')
    except Exception as e:
        print(f'{itype}: ERROR {e}')

print('\n=== PROBANDO TIPOS DE MARGEN ===')
margin_types = ['forex','stocks','crypto','commodities','indices','etf','cfd','margin','leverage']
for itype in margin_types:
    try:
        api.api.send_websocket_request('sendMessage', {
            'name': 'get-instruments',
            'version': '3.0',
            'body': {'type': itype}
        })
        time.sleep(1.5)
        from iqoptionapi import global_value as gv
        data = getattr(gv, 'instruments', {})
        count = len(data.get(itype, {}))
        print(f'{itype:20s}: {count} activos en global_value')
    except Exception as e:
        print(f'{itype:20s}: ERROR {e}')

print('\n=== TURBO VS BINARY EXPIRATIONS ===')
ot = api.get_all_open_time()
for cat in ['turbo','binary']:
    assets = ot.get(cat, {})
    if assets:
        sample = list(assets.items())[0]
        print(f'{cat}: {sample[0]} -> {sample[1]}')
