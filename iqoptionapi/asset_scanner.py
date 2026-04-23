"""
iqoptionapi/asset_scanner.py
────────────────────────────
Filtrador de activos operables en tiempo real.
"""
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from typing import List, Dict, Optional
from iqoptionapi.strategy.indicators import ema, atr


@dataclass(frozen=True)
class AssetScore:
    asset:          str
    payout_pct:     float
    is_open:        bool
    volatility:     float   # ATR normalizado
    score:          float
    reason:         str

class AssetScanner:
    """
    Califica activos usando Payout, Volatilidad y Tendencia.
    """

    def __init__(
        self,
        min_payout: float = 0.80,
        optimal_vol: float = 0.40,
    ) -> None:
        self.min_payout = min_payout
        self.optimal_vol = optimal_vol

    def score_asset(
        self,
        asset: str,
        candles: NDArray[np.float64],
        payout: float,
        is_open: bool = True
    ) -> AssetScore:
        """
        Calcula el score de un activo.
        """
        if not is_open or payout < self.min_payout:
            return AssetScore(asset, payout, is_open, 0.0, 0.0, "Closed or low payout")

        if len(candles) < 30:
            return AssetScore(asset, payout, is_open, 0.0, 0.0, "Insufficient data")

        closes = candles[:, 3]
        highs = candles[:, 1]
        lows = candles[:, 2]

        # 1. Volatility Score (ATR normalizado)
        current_atr = atr(highs, lows, closes, period=14)
        if np.isnan(current_atr) or closes[-1] == 0:
            return AssetScore(asset, payout, is_open, 0.0, 0.0, "ATR calc failed")
            
        norm_vol = current_atr / closes[-1]
        # Escalado simple para el ejemplo (0.0 a 0.005 suele ser rango forex normalizado)
        # Ajustamos para que 0.4 sea "óptimo" según especificación (escalado arbitrario para el score)
        vol_score = 1.0 - abs(norm_vol * 1000 - self.optimal_vol) / max(0.001, self.optimal_vol)
        vol_score = max(0.0, min(1.0, vol_score))

        # 2. Trend Score (|EMA9 - EMA21| / price)
        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        trend_score = abs(ema9 - ema21) / closes[-1]
        trend_score = min(1.0, trend_score * 500) # Escalado para normalizar 0-1

        # 3. Composite Score
        # score = (payout * 0.5) + (volatility_score * 0.3) + (trend_score * 0.2)
        final_score = (payout * 0.5) + (vol_score * 0.3) + (trend_score * 0.2)
        
        reason = f"P:{payout:.2f} V:{vol_score:.2f} T:{trend_score:.2f}"
        
        return AssetScore(
            asset=asset,
            payout_pct=payout,
            is_open=is_open,
            volatility=norm_vol,
            score=round(float(final_score), 3),
            reason=reason
        )

    def get_best_assets(
        self,
        asset_list: List[str],
        candles_map: Dict[str, NDArray[np.float64]],
        payouts_map: Dict[str, float],
        top_n: int = 3,
    ) -> List[AssetScore]:
        scores = []
        for asset in asset_list:
            if asset in candles_map and asset in payouts_map:
                score_obj = self.score_asset(asset, candles_map[asset], payouts_map[asset])
                if score_obj.score > 0:
                    scores.append(score_obj)
        
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:top_n]

    def is_worth_trading(self, score_obj: AssetScore, min_score: float = 0.6) -> bool:
        return score_obj.score >= min_score
