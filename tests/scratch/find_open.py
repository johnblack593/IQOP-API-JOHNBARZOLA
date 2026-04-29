from iqoptionapi.stable_api import IQ_Option
import os
from dotenv import load_dotenv

load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()

print("Buscando un activo turbo abierto...")
ALL_Asset = api.get_all_open_time()
for type_name, data in ALL_Asset.items():
    if type_name == "turbo":
        for asset, is_open in data.items():
            if is_open["open"]:
                print(f"Abierto: {asset}")
                break
