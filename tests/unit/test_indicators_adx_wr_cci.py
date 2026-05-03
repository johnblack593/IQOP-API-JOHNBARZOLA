"""
Unit tests for ADX, Williams %R, and CCI indicators.
"""

import numpy as np
import pytest
from iqoptionapi.strategy.indicators import adx, williams_r, cci


# --- ADX TESTS ---

def test_adx_returns_nan_for_insufficient_data():
    """len(closes) < period*2 -> todo nan."""
    period = 14
    closes = np.random.random(period * 2 - 1)
    highs = closes + 1
    lows = closes - 1
    res = adx(highs, lows, closes, period=period)
    assert np.all(np.isnan(res))


def test_adx_shape_matches_input():
    """Con 50 velas, adx(...) tiene len == 50."""
    period = 14
    closes = np.random.random(50)
    highs = closes + 1
    lows = closes - 1
    res = adx(highs, lows, closes, period=period)
    assert len(res) == 50


def test_adx_values_in_valid_range():
    """ADX válido (no-nan) debe estar en [0, 100]."""
    period = 14
    closes = np.linspace(10, 20, 100)  # Strong trend
    highs = closes + 0.5
    lows = closes - 0.5
    res = adx(highs, lows, closes, period=period)
    valid_values = res[~np.isnan(res)]
    assert len(valid_values) > 0
    assert np.all(valid_values >= 0)
    assert np.all(valid_values <= 100)


def test_adx_accepts_python_lists():
    """No debe lanzar TypeError con listas Python."""
    # Necesitamos al menos 28 elementos para period=14
    h = [10] * 30
    l = [8] * 30
    c = [9] * 30
    res = adx(h, l, c, period=14)
    assert isinstance(res, np.ndarray)


# --- WILLIAMS %R TESTS ---

def test_williams_r_returns_nan_for_insufficient_data():
    """len < period -> todo nan."""
    res = williams_r([10], [8], [9], period=14)
    assert np.all(np.isnan(res))


def test_williams_r_range_is_minus100_to_0():
    """Todos los valores válidos (no-nan) están en [-100, 0]."""
    closes = np.random.random(50) * 10
    highs = closes + np.random.random(50)
    lows = closes - np.random.random(50)
    res = williams_r(highs, lows, closes, period=14)
    valid_values = res[~np.isnan(res)]
    assert np.all(valid_values >= -100)
    assert np.all(valid_values <= 0)


def test_williams_r_known_value():
    """
    Calcular manualmente para period=1:
    H=[10], L=[8], C=[9] -> %R = (10-9)/(10-8)*-100 = -50.0
    """
    res = williams_r([10], [8], [9], period=1)
    assert res[0] == -50.0


def test_williams_r_zero_range_returns_nan():
    """Si high == low en toda la ventana -> nan."""
    res = williams_r([10, 10], [10, 10], [10, 10], period=2)
    assert np.isnan(res[1])


# --- CCI TESTS ---

def test_cci_returns_nan_for_insufficient_data():
    """len < period -> todo nan."""
    res = cci([10], [8], [9], period=20)
    assert np.all(np.isnan(res))


def test_cci_shape_matches_input():
    """Con 30 velas, cci(..., period=20) tiene len == 30."""
    closes = np.random.random(30)
    res = cci(closes+1, closes-1, closes, period=20)
    assert len(res) == 30


def test_cci_known_value():
    """
    Con period=1 y una sola vela H=10,L=8,C=9:
    TP = 9.0, SMA_TP = 9.0, mean_dev = 0.0 -> nan
    """
    res = cci([10], [8], [9], period=1)
    assert np.isnan(res[0])


def test_cci_accepts_python_lists():
    """No debe lanzar TypeError con listas Python."""
    h = [10] * 25
    l = [8] * 25
    c = [9] * 25
    res = cci(h, l, c, period=20)
    assert isinstance(res, np.ndarray)
