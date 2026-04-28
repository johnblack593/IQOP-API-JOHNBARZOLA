import os
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
api.connect()

init_v2 = api.get_all_init_v2()

group_counts = {}
group_samples = {}

for cat in ['binary', 'turbo', 'blitz']:
    if cat in init_v2:
        actives = init_v2[cat].get('actives', {})
        for a_id, info in actives.items():
            g_id = info.get('group_id')
            if g_id is not None:
                group_counts[g_id] = group_counts.get(g_id, 0) + 1
                if g_id not in group_samples:
                    group_samples[g_id] = []
                if len(group_samples[g_id]) < 3:
                    group_samples[g_id].append(info.get('name'))

print("Group IDs found:")
for g_id, count in sorted(group_counts.items()):
    print(f"Group {g_id}: {count} actives -> {group_samples[g_id]}")

api.close()
