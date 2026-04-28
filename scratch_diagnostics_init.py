import os
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()

init_v2 = api.get_all_init_v2()
if init_v2:
    print("KEYS in init_v2:", init_v2.keys())
    for cat in ['forex', 'stocks', 'crypto', 'commodities', 'indices', 'etf', 'cfd']:
        if cat in init_v2:
            print(f"{cat}: {len(init_v2[cat].get('actives', {}))} activos en init_v2")
        else:
            print(f"{cat}: NO EXISTE en init_v2")
api.close()
