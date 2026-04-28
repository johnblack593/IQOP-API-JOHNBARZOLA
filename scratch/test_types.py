from iqoptionapi.stable_api import IQ_Option
import os
from dotenv import load_dotenv
load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()
api.change_balance('PRACTICE')
print("Type of game_betinfo:", type(api.api.game_betinfo))
print("Type of game_betinfo_event:", type(api.api.game_betinfo_event))
