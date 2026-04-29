import json
import os

# Load handlers from client.py (manual copy-paste of the keys for speed)
handlers = [
    'api_game_betinfo_result', 'api_game_getoptions_result', 'api_option_init_all_result',
    'auto-margin-call-changed', 'available-leverages', 'balances', 'balance-changed',
    'buyComplete', 'candles', 'candle-generated', 'candles-generated',
    'client-price-generated', 'commission-changed', 'deferred-orders',
    'digital-option-placed', 'financial-information', 'heartbeat',
    'history-positions', 'initialization-data', 'instruments',
    'instrument-quotes-generated', 'leaderboard-deals-client',
    'leaderboard-userinfo-deals-client', 'listInfoData', 'live-deal',
    'live-deal-binary-option-placed', 'live-deal-digital-option', 'option',
    'option-closed', 'option-opened', 'order', 'order-canceled',
    'order-placed-temp', 'overnight-fee', 'position', 'positions',
    'position-changed', 'position-closed', 'position-history', 'profile',
    'result', 'socket-option-closed', 'socket-option-opened', 'sold-options',
    'strike-list', 'technical-indicators', 'timeSync', 'top-assets-updated',
    'tpsl-changed', 'traders-mood-changed', 'training-balance-reset',
    'underlying-list', 'users-availability', 'user-profile-client'
]

missing = set()
found = set()

file_path = 'examples/debug_ws_messages.json'
if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
            for msg in data:
                name = msg.get('name')
                if name:
                    found.add(name)
                    if name not in handlers:
                        missing.add(name)
        except:
            # Maybe it's a line-delimited JSON?
            f.seek(0)
            for line in f:
                try:
                    msg = json.loads(line)
                    name = msg.get('name')
                    if name:
                        found.add(name)
                        if name not in handlers:
                            missing.add(name)
                except:
                    pass

print("Unique messages found in JSON:", sorted(list(found)))
print("Missing handlers for:", sorted(list(missing)))
