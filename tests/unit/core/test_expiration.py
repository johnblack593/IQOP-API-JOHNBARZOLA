import time
from iqoptionapi.expiration import get_expiration_time

def test_get_expiration_time_binary():
    # get_expiration_time returns (timestamp, index)
    exp, idx = get_expiration_time(int(time.time()), 1)
    assert isinstance(exp, int)
    assert exp > time.time()

def test_get_expiration_time_digital():
    # Digital usa duraciones fijas (1, 5, 15)
    exp, idx = get_expiration_time(int(time.time()), 5)
    assert isinstance(exp, int)
    assert exp > time.time()

def test_expiration_not_in_past():
    now = int(time.time())
    exp, idx = get_expiration_time(now, 1)
    assert exp >= now

def test_expiration_duration_1m():
    now = int(time.time())
    exp, idx = get_expiration_time(now, 1)
    # Por el protocolo de IQ, suele ser el próximo minuto 00 o +60s
    assert exp > now

def test_expiration_duration_5m():
    now = int(time.time())
    exp, idx = get_expiration_time(now, 5)
    assert exp > now
