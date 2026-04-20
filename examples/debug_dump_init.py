import os
import json
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
api.connect()

init_data = api.api.api_option_init_all_result_v2
with open("examples/debug_init_data.json", "w") as f:
    json.dump(init_data, f, indent=2)

print("init data dumped to examples/debug_init_data.json!")
api.close()
