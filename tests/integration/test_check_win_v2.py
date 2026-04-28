from iqoptionapi.stable_api import IQ_Option
import os
from dotenv import load_dotenv
load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()
api.change_balance('PRACTICE')
print("Testing check_win_v2...")
res = api.check_win_v2(12345, timeout=1.0)
print("Result:", res)
