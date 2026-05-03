"""
Unit tests for VWAP and OBV indicators in iqoptionapi.strategy.indicators.
"""

import numpy as np
import pytest
from iqoptionapi.strategy.indicators import vwap, obv


# --- VWAP TESTS ---

def test_vwap_basic_calculation():
    """Con valores conocidos, verificar resultado numérico exacto."""
    # Vela 1: H=10, L=8, C=9, V=100 -> TP=9, TP*V=900, CumTPV=900, CumV=100, VWAP=9.0
    # Vela 2: H=12, L=10, C=11, V=200 -> TP=11, TP*V=2200, CumTPV=3100, CumV=300, VWAP=10.333333
    highs = [10, 12]
    lows = [8, 10]
    closes = [9, 11]
    volumes = [100, 200]
    
    res = vwap(highs, lows, closes, volumes)
    
    expected = [9.0, 3100 / 300]
    np.testing.assert_allclose(res, expected, rtol=1e-6)


def test_vwap_empty_input_returns_empty():
    """vwap([], [], [], []) -> array vacío."""
    res = vwap([], [], [], [])
    assert len(res) == 0
    assert isinstance(res, np.ndarray)


def test_vwap_all_zero_volume_returns_nan():
    """Si todos los volúmenes son 0 -> resultado es nan en cada posición."""
    highs = [10, 11]
    lows = [9, 10]
    closes = [10, 11]
    volumes = [0, 0]
    
    res = vwap(highs, lows, closes, volumes)
    assert np.all(np.isnan(res))


def test_vwap_mismatched_lengths_returns_nan_array():
    """vwap([1,2,3], [1,2], [1,2,3], [1,2,3]) -> array de nan del tamaño de closes."""
    res = vwap([1, 2, 3], [1, 2], [1, 2, 3], [1, 2, 3])
    assert len(res) == 3
    assert np.all(np.isnan(res))


def test_vwap_accepts_python_lists():
    """Pasar listas Python no debe lanzar TypeError."""
    res = vwap([10], [8], [9], [100])
    assert isinstance(res, np.ndarray)
    assert res[0] == 9.0


def test_vwap_single_candle():
    """Con 1 vela: resultado debe ser igual a typical_price[0]."""
    res = vwap([10], [8], [9], [100])
    assert res[0] == 9.0


# --- OBV TESTS ---

def test_obv_basic_rising_closes():
    """Closes=[10,11,12], volumes=[100,200,300] -> OBV = [0, 200, 500]."""
    closes = [10, 11, 12]
    volumes = [100, 200, 300]
    res = obv(closes, volumes)
    expected = [0.0, 200.0, 500.0]
    np.testing.assert_allclose(res, expected)


def test_obv_basic_falling_closes():
    """Closes=[12,11,10], volumes=[100,200,300] -> OBV = [0, -200, -500]."""
    closes = [12, 11, 10]
    volumes = [100, 200, 300]
    res = obv(closes, volumes)
    expected = [0.0, -200.0, -500.0]
    np.testing.assert_allclose(res, expected)


def test_obv_flat_closes_no_change():
    """Closes=[10,10,10], volumes=[100,200,300] -> OBV = [0, 0, 0]."""
    closes = [10, 10, 10]
    volumes = [100, 200, 300]
    res = obv(closes, volumes)
    expected = [0.0, 0.0, 0.0]
    np.testing.assert_allclose(res, expected)


def test_obv_single_element():
    """closes=[5], volumes=[100] -> OBV = [0.0]."""
    res = obv([5], [100])
    assert len(res) == 1
    assert res[0] == 0.0
