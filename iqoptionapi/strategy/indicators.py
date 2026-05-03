"""
iqoptionapi/strategy/indicators.py
────────────────────────────────────
Funciones puras de indicadores técnicos.
Input: numpy arrays de precios (close, high, low, volume).
Output: float o numpy array.

REGLAS:
- Todas las funciones son puras — sin estado, sin efectos secundarios.
- Si los datos son insuficientes, retornar float('nan').
- Usar solo numpy (sin TA-Lib, sin pandas salvo donde se indique).
- Todas las funciones tienen type hints y docstring con fórmula.
"""
import numpy as np
from numpy.typing import NDArray


def sma(prices: NDArray[np.float64], period: int) -> float:
    """
    Simple Moving Average.
    SMA = sum(prices[-period:]) / period
    Retorna nan si len(prices) < period.
    """
    if len(prices) < period:
        return float('nan')
    return float(np.mean(prices[-period:]))


def ema(prices: NDArray[np.float64], period: int) -> float:
    """
    Exponential Moving Average (usando factor de suavizado k=2/(period+1)).
    Retorna nan si len(prices) < period.
    """
    if len(prices) < period:
        return float('nan')
    
    k = 2 / (period + 1)
    # Start with SMA of the first 'period' elements
    current_ema = np.mean(prices[:period])
    
    # Iterate through the rest
    for price in prices[period:]:
        current_ema = (price * k) + (current_ema * (1 - k))
        
    return float(current_ema)


def rsi(prices: NDArray[np.float64], period: int = 14) -> float:
    """
    Relative Strength Index.
    RSI = 100 - (100 / (1 + RS))
    RS = avg_gain / avg_loss (Wilder's smoothing)
    Retorna nan si len(prices) < period + 1.
    Rango: 0–100. Sobrecompra > 70, sobreventa < 30.
    """
    if len(prices) < period + 1:
        return float('nan')
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    
    # Initial averages (SMA)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    # Wilder's smoothing
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    return float(100.0 - (100.0 / (1.0 + rs)))


def _ema_array(prices: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """Helper to get EMA as an array."""
    if len(prices) < period:
        return np.full(len(prices), np.nan)
    
    emas = np.full(len(prices), np.nan)
    k = 2 / (period + 1)
    emas[period-1] = np.mean(prices[:period])
    
    for i in range(period, len(prices)):
        emas[i] = (prices[i] * k) + (emas[i-1] * (1 - k))
        
    return emas


def macd(
    prices: NDArray[np.float64],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[float, float, float]:
    """
    MACD Line, Signal Line, Histogram.
    MACD    = EMA(fast) - EMA(slow)
    Signal  = EMA(MACD, signal_period)
    Hist    = MACD - Signal
    Retorna (nan, nan, nan) si datos insuficientes.
    """
    if len(prices) < slow + signal:
        return (float('nan'), float('nan'), float('nan'))
    
    ema_fast = _ema_array(prices, fast)
    ema_slow = _ema_array(prices, slow)
    
    macd_line = ema_fast - ema_slow
    
    # Calculate Signal line (EMA of MACD line)
    # We need to strip NaNs for EMA calculation
    valid_macd = macd_line[~np.isnan(macd_line)]
    if len(valid_macd) < signal:
        return (float('nan'), float('nan'), float('nan'))
    
    signal_line_array = _ema_array(valid_macd, signal)
    
    current_macd = macd_line[-1]
    current_signal = signal_line_array[-1]
    current_hist = current_macd - current_signal
    
    return (float(current_macd), float(current_signal), float(current_hist))


def bollinger_bands(
    prices: NDArray[np.float64],
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[float, float, float]:
    """
    Bollinger Bands: (upper, middle, lower).
    middle = SMA(period)
    upper  = middle + num_std * std(prices[-period:])
    lower  = middle - num_std * std(prices[-period:])
    Retorna (nan, nan, nan) si datos insuficientes.
    """
    if len(prices) < period:
        return (float('nan'), float('nan'), float('nan'))
    
    window = prices[-period:]
    middle = np.mean(window)
    std = np.std(window)
    
    upper = middle + (num_std * std)
    lower = middle - (num_std * std)
    
    return (float(upper), float(middle), float(lower))


def stochastic(
    highs: NDArray[np.float64],
    lows: NDArray[np.float64],
    closes: NDArray[np.float64],
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[float, float]:
    """
    Stochastic Oscillator: (%K, %D).
    %K = (close - lowest_low) / (highest_high - lowest_low) * 100
    %D = SMA(%K, d_period)
    Retorna (nan, nan) si datos insuficientes.
    """
    if len(highs) < k_period + d_period:
        return (float('nan'), float('nan'))
    
    # Calculate %K for the last 'd_period' points to get SMA for %D
    k_values = []
    for i in range(d_period):
        end = len(highs) - i
        start = end - k_period
        
        current_close = closes[end-1]
        lowest_low = np.min(lows[start:end])
        highest_high = np.max(highs[start:end])
        
        if highest_high == lowest_low:
            k = 50.0
        else:
            k = (current_close - lowest_low) / (highest_high - lowest_low) * 100
        k_values.append(k)
        
    current_k = k_values[0]
    current_d = np.mean(k_values) # SMA of %K
    
    return (float(current_k), float(current_d))


def atr(
    highs: NDArray[np.float64],
    lows: NDArray[np.float64],
    closes: NDArray[np.float64],
    period: int = 14,
) -> float:
    """
    Average True Range.
    TR = max(high-low, |high-prev_close|, |low-prev_close|)
    ATR = EMA(TR, period)
    Retorna nan si datos insuficientes.
    """
    if len(highs) < period + 1:
        return float('nan')
    
    tr_values = []
    for i in range(1, len(highs)):
        h = highs[i]
        l = lows[i]
        pc = closes[i-1]
        
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_values.append(tr)
        
    # ATR is the EMA of TR
    return ema(np.array(tr_values, dtype=np.float64), period)


def vwap(
    highs: NDArray[np.float64],
    lows: NDArray[np.float64],
    closes: NDArray[np.float64],
    volumes: NDArray[np.float64],
) -> NDArray[np.float64]:
    """
    Volume Weighted Average Price.
    VWAP = sum(TypicalPrice * Volume) / sum(Volume)
    TypicalPrice = (High + Low + Close) / 3
    Retorna array de nan si longitudes no coinciden.
    """
    h = np.asarray(highs, dtype=np.float64)
    l = np.asarray(lows, dtype=np.float64)
    c = np.asarray(closes, dtype=np.float64)
    v = np.asarray(volumes, dtype=np.float64)

    if len(c) < 1:
        return np.array([], dtype=np.float64)

    if not (len(h) == len(l) == len(c) == len(v)):
        return np.full(len(c), np.nan, dtype=np.float64)

    typical_price = (h + l + c) / 3.0
    tp_v = typical_price * v

    cum_tp_v = np.cumsum(tp_v)
    cum_v = np.cumsum(v)

    # Avoid division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        res = cum_tp_v / cum_v
        res[cum_v == 0] = np.nan

    return res


def obv(
    closes: NDArray[np.float64],
    volumes: NDArray[np.float64],
) -> NDArray[np.float64]:
    """
    On-Balance Volume.
    OBV[i] = OBV[i-1] + Volume[i] if close[i] > close[i-1]
    OBV[i] = OBV[i-1] - Volume[i] if close[i] < close[i-1]
    Retorna array de nan si longitudes no coinciden.
    """
    c = np.asarray(closes, dtype=np.float64)
    v = np.asarray(volumes, dtype=np.float64)

    if len(c) < 1:
        return np.array([], dtype=np.float64)
    if len(c) == 1:
        return np.array([0.0], dtype=np.float64)

    if len(c) != len(v):
        return np.full(len(c), np.nan, dtype=np.float64)

    diff = np.diff(c)
    direction = np.sign(diff)

    # OBV start at 0
    res = np.zeros(len(c), dtype=np.float64)
    res[1:] = np.cumsum(direction * v[1:])

    return res


def adx(
    highs: NDArray[np.float64],
    lows: NDArray[np.float64],
    closes: NDArray[np.float64],
    period: int = 14,
) -> NDArray[np.float64]:
    """
    Average Directional Index (Wilder's).
    Measure trend strength. Rango: 0-100.
    Retorna array de nan si datos insuficientes (requiere 2*period).
    """
    h = np.asarray(highs, dtype=np.float64)
    l = np.asarray(lows, dtype=np.float64)
    c = np.asarray(closes, dtype=np.float64)

    if len(c) < period * 2:
        return np.full(len(c), np.nan, dtype=np.float64)

    if not (len(h) == len(l) == len(c)):
        return np.full(len(c), np.nan, dtype=np.float64)

    # 1. True Range
    tr = np.zeros(len(c))
    tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(
        h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1]))
    )

    # 2. Directional Movement
    up_move = h[1:] - h[:-1]
    down_move = l[:-1] - l[1:]

    plus_dm = np.zeros(len(c))
    minus_dm = np.zeros(len(c))

    plus_dm[1:] = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm[1:] = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    # 3. Smoothed TR, +DM, -DM (Wilder's Smoothing)
    def _wilder(vals: NDArray[np.float64], n: int) -> NDArray[np.float64]:
        res = np.full(len(vals), np.nan)
        res[n] = np.sum(vals[1 : n + 1])  # Start at period index
        for i in range(n + 1, len(vals)):
            res[i] = res[i - 1] - (res[i - 1] / n) + vals[i]
        return res

    atr_w = _wilder(tr, period)
    plus_di_w = _wilder(plus_dm, period)
    minus_di_w = _wilder(minus_dm, period)

    # 4. DI
    plus_di = 100 * plus_di_w / atr_w
    minus_di = 100 * minus_di_w / atr_w

    # 5. DX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)

    # 6. ADX (Smoothing of DX)
    # The first valid DX is at index period. We smooth it starting from there.
    # Wilder smoothing for ADX typically starts at period*2 - 1
    adx_res = np.full(len(c), np.nan)
    start_idx = period * 2 - 1
    if len(dx) > start_idx:
        valid_dx = dx[period : start_idx + 1]
        adx_res[start_idx] = np.mean(valid_dx)
        for i in range(start_idx + 1, len(c)):
            adx_res[i] = (adx_res[i - 1] * (period - 1) + dx[i]) / period

    return adx_res


def williams_r(
    highs: NDArray[np.float64],
    lows: NDArray[np.float64],
    closes: NDArray[np.float64],
    period: int = 14,
) -> NDArray[np.float64]:
    """
    Williams %R.
    %R = (HighestHigh - Close) / (HighestHigh - LowestLow) * -100
    Retorna nan si rango es 0.
    """
    h = np.asarray(highs, dtype=np.float64)
    l = np.asarray(lows, dtype=np.float64)
    c = np.asarray(closes, dtype=np.float64)

    if len(c) < period:
        return np.full(len(c), np.nan, dtype=np.float64)

    if not (len(h) == len(l) == len(c)):
        return np.full(len(c), np.nan, dtype=np.float64)

    res = np.full(len(c), np.nan)

    for i in range(period - 1, len(c)):
        hh = np.max(h[i - period + 1 : i + 1])
        ll = np.min(l[i - period + 1 : i + 1])
        diff = hh - ll
        if diff != 0:
            res[i] = (hh - c[i]) / diff * -100.0

    return res


def cci(
    highs: NDArray[np.float64],
    lows: NDArray[np.float64],
    closes: NDArray[np.float64],
    period: int = 20,
) -> NDArray[np.float64]:
    """
    Commodity Channel Index.
    CCI = (TypicalPrice - SMA_TP) / (0.015 * MeanDeviation)
    """
    h = np.asarray(highs, dtype=np.float64)
    l = np.asarray(lows, dtype=np.float64)
    c = np.asarray(closes, dtype=np.float64)

    if len(c) < period:
        return np.full(len(c), np.nan, dtype=np.float64)

    if not (len(h) == len(l) == len(c)):
        return np.full(len(c), np.nan, dtype=np.float64)

    tp = (h + l + c) / 3.0
    res = np.full(len(c), np.nan)

    for i in range(period - 1, len(c)):
        window = tp[i - period + 1 : i + 1]
        sma_tp = np.mean(window)
        mean_dev = np.mean(np.abs(window - sma_tp))
        if mean_dev != 0:
            res[i] = (tp[i] - sma_tp) / (0.015 * mean_dev)

    return res
