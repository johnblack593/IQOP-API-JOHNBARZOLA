import os, time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.core.time_sync import _clock

load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
ok, msg = api.connect()
assert ok, f"Conexion fallida: {msg}"
api.change_balance('PRACTICE')
time.sleep(2)
ot = api.get_all_open_time()
blitz = [k for k,v in ot.get('blitz',{}).items() if v.get('open')]

if not blitz:
    print("Sin activos Blitz. Usando un EURUSD-OTC falso para ver si da error de cierre...")
    blitz = ["EURUSD-OTC"]

asset = next((a for a in ['EURUSD-OTC','GBPUSD-OTC'] if a in blitz), blitz[0])
for i in range(5):
    offset_pre = _clock.offset_seconds()
    try:
        status, oid = api.buy_blitz(asset, 'call', 1.0, 30)
        print(f'Blitz {i+1}: status={status} oid={oid} offset_pre={offset_pre:.3f}s')
        if status:
            time.sleep(35)
            offset_post = _clock.offset_seconds()
            print(f'  offset_post={offset_post:.3f}s | drift={abs(offset_post-offset_pre):.3f}s')
            assert abs(offset_post) < 5.0, f'Clock drift CRITICO: {offset_post:.3f}s'
        else:
            print("  Falló compra Blitz, reintentando...")
            time.sleep(2)
    except Exception as e:
        print("  Error en buy_blitz:", e)
        time.sleep(2)
print('BLITZ STRESS: PASADO')

