"""
tests/live/helpers/candle_loader.py
────────────────────────────────────
Helper para descargar y convertir velas a numpy arrays.
"""
import time
import numpy as np
from numpy.typing import NDArray
from iqoptionapi.stable_api import IQ_Option

def get_live_candles(
    api: IQ_Option, 
    asset: str, 
    size: int, 
    count: int
) -> NDArray[np.float64]:
    """
    Descarga velas reales y las convierte a array numpy (N, 6).
    Formato: [from, open, max, min, close, volume]
    """
    candles = api.get_candles(asset, size, count, time.time())
    if not candles or not isinstance(candles, list):
        return np.array([], dtype=np.float64)
    
    data = []
    for c in candles:
        data.append([
            float(c['from']),
            float(c['open']),
            float(c['max']),
            float(c['min']),
            float(c['close']),
            float(c['volume'])
        ])
    
    return np.array(data, dtype=np.float64)
