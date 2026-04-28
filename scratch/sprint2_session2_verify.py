import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: Verificar que _CFD_GROUP_IDS no contiene IDs de GROUP_ID_TO_TYPE
from iqoptionapi.http.instruments import GROUP_ID_TO_TYPE, _CFD_GROUP_IDS, _classify_type

conflicts = set(GROUP_ID_TO_TYPE.keys()) & _CFD_GROUP_IDS
assert not conflicts, f"CONFLICTO: IDs {conflicts} estan en ambos dicts"
print(f"[OK] Sin conflictos en GROUP_ID_TO_TYPE vs _CFD_GROUP_IDS")

# Test 2: Verificar clasificacion correcta
assert _classify_type(1)  == "forex",       "group 1 debe ser forex"
assert _classify_type(2)  == "stocks",      "group 2 debe ser stocks"
assert _classify_type(3)  == "commodities", "group 3 debe ser commodities"
assert _classify_type(4)  == "indices",     "group 4 debe ser indices"
assert _classify_type(16) == "crypto",      "group 16 debe ser crypto"
assert _classify_type(41) == "etf",         "group 41 debe ser etf"
assert _classify_type(5)  == "cfd",         "group 5 debe ser cfd (generico)"
print("[OK] Clasificacion de group_id correcta para todos los tipos")

# Test 3: Verificar WARP availability check y rate limit detection
from iqoptionapi.ip_rotation import is_warp_available, is_rate_limit_error, get_ip_geo
print(f"[INFO] warp-cli disponible: {is_warp_available()}")
assert is_rate_limit_error("auth timeout")        == True
assert is_rate_limit_error("429 too many requests") == True
assert is_rate_limit_error("invalid password")    == False
print("[OK] is_rate_limit_error detecta senales correctamente")

# Test 4: Verificar geo diagnostic (solo informativo, no bloquea)
geo = get_ip_geo()
if geo:
    print(f"[INFO] IP actual: {geo['ip']} ({geo['country']}/{geo['city']})")
    print(f"[INFO] Geo-check es solo diagnostico, NO bloquea conexiones")
else:
    print("[INFO] No se pudo obtener geo (offline o timeout)")

print("\nSprint 2/3 - todos los checks pasaron")
