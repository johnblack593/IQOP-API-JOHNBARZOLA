"""
verify_cfd_post_kyc.py -- Diagnose CFD KYC status
TVC-FIX-20260427-CFDKYC
"""
import os, sys, time, json, logging
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

logging.basicConfig(level=logging.WARNING)
load_dotenv()

api = IQ_Option(os.getenv('IQ_EMAIL'), os.getenv('IQ_PASSWORD'))
ok, msg = api.connect()
if not ok:
    print(f"CONEXION FALLIDA: {msg}")
    sys.exit(1)

api.change_balance("PRACTICE")
time.sleep(3)

# Check CFD capability flag
cfd_capable = getattr(api, '_cfd_order_capable', None)
print(f"CFD order capable flag: {cfd_capable}")

# Get init data to check available groups
init_v2 = api.get_all_init_v2()
group_counts = {}
if init_v2:
    for cat in ['binary', 'turbo', 'blitz']:
        if cat in init_v2:
            for a_id, info in init_v2[cat].get('actives', {}).items():
                g_id = info.get('group_id')
                if g_id is not None:
                    group_counts[g_id] = group_counts.get(g_id, 0) + 1

    print(f"\nGroup ID distribution (from init_v2):")
    from iqoptionapi.http.instruments import _classify_type
    for g_id, count in sorted(group_counts.items()):
        print(f"  Group {g_id:3d} ({_classify_type(g_id):15s}): {count} activos")

# Try CFD instrument discovery
print("\n--- CFD Instrument Discovery ---")
for itype in ['cfd', 'forex', 'crypto', 'stocks', 'commodities', 'indices', 'etf']:
    try:
        result = api.get_instruments(itype)
        instruments = []
        if isinstance(result, dict):
            instruments = result.get('instruments', [])
        count = len(instruments)
        open_count = sum(1 for ins in instruments if ins.get('enabled') and not ins.get('is_suspended'))
        src = instruments[0].get('_source', 'ws') if instruments else 'N/A'
        print(f"  {itype:15s}: {count:4d} total | {open_count:4d} abiertos | source={src}")
    except Exception as e:
        print(f"  {itype:15s}: ERROR {e}")

# Try buy_order for CFD (the actual test)
print("\n--- CFD buy_order Test ---")
# First check CFD capability via check_cfd_order_capability
try:
    cap = api.check_cfd_order_capability()
    print(f"check_cfd_order_capability: {cap}")
except Exception as e:
    print(f"check_cfd_order_capability error: {e}")

# Try with AAPL
test_assets = ['AAPL', 'EURUSD', 'BTCUSD']
for asset in test_assets:
    for itype in ['cfd', 'stocks', 'forex', 'crypto']:
        try:
            status, order_id = api.buy_order(
                instrument_type=itype,
                instrument_id=asset,
                side="buy",
                amount=1,
                leverage=1,
                type="market"
            )
            print(f"  buy_order({asset}, type={itype}): status={status} order={order_id}")
            if status and order_id:
                time.sleep(3)
                try:
                    close_ok = api.close_position(order_id)
                    print(f"    close_position: {close_ok}")
                except Exception as e:
                    print(f"    close_position error: {e}")
                break  # Success, no need to try other types
        except Exception as e:
            print(f"  buy_order({asset}, type={itype}): EXCEPTION {e}")

try: api.close()
except: pass
