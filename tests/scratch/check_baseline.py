from iqoptionapi.stable_api import IQ_Option
import os
from dotenv import load_dotenv
load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
ok, msg = api.connect()
print('CONEXION:', ok, msg)
api.change_balance('PRACTICE')
import time; time.sleep(1)
print('BALANCE:', api.get_balance())
ot = api.get_all_open_time()
digital = [k for k,v in ot.get('digital',{}).items() if v.get('open')]
turbo   = [k for k,v in ot.get('turbo',{}).items()   if v.get('open')]
cfd     = [k for k,v in ot.get('cfd',{}).items()     if v.get('open')]
print('DIGITAL abiertos:', len(digital))
print('TURBO abiertos:', len(turbo))
print('CFD abiertos:', len(cfd))
