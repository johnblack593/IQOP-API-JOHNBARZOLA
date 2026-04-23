"""
iqoptionapi/performance.py
──────────────────────────
Calculadora de métricas de rendimiento profesionales.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np
from iqoptionapi.trade_journal import TradeRecord


@dataclass(frozen=True)
class PerformanceReport:
    period_start:       datetime
    period_end:         datetime
    total_trades:       int
    wins:               int
    losses:             int
    draws:              int
    winrate:            float
    profit_factor:      float
    total_pnl_usd:      float
    max_drawdown_usd:   float
    max_drawdown_pct:   float
    sharpe_ratio:       float
    avg_win_usd:        float
    avg_loss_usd:       float
    largest_win_usd:    float
    largest_loss_usd:   float
    max_consecutive_wins:   int
    max_consecutive_losses: int
    avg_confidence:         float
    best_asset:             str
    best_strategy:          str
    best_hour:              int

class PerformanceAnalyzer:
    """
    Calcula métricas a partir de listas de TradeRecord.
    """

    @staticmethod
    def analyze(trades: List[TradeRecord]) -> PerformanceReport:
        if not trades:
            now = datetime.now()
            return PerformanceReport(
                now, now, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0, 0, 0.0, "", "", 0
            )

        # Sort by open_time
        trades = sorted(trades, key=lambda x: x.open_time)
        
        wins = [t for t in trades if t.result == "win"]
        losses = [t for t in trades if t.result == "loss"]
        draws = [t for t in trades if t.result == "draw"]
        
        gross_profit = sum(t.profit_usd for t in wins if t.profit_usd)
        gross_loss = abs(sum(t.profit_usd for t in losses if t.profit_usd))
        
        winrate = len(wins) / (len(wins) + len(losses)) if (len(wins) + len(losses)) > 0 else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)
        
        pnl_sequence = [t.profit_usd for t in trades if t.profit_usd is not None]
        total_pnl = sum(pnl_sequence)
        
        max_dd_usd, max_dd_pct = PerformanceAnalyzer.max_drawdown(trades)
        
        # Consecutive wins/losses
        max_c_wins = 0
        max_c_losses = 0
        current_c_wins = 0
        current_c_losses = 0
        for t in trades:
            if t.result == "win":
                current_c_wins += 1
                current_c_losses = 0
            elif t.result == "loss":
                current_c_losses += 1
                current_c_wins = 0
            max_c_wins = max(max_c_wins, current_c_wins)
            max_c_losses = max(max_c_losses, current_c_losses)

        # Best asset/strategy/hour
        assets = {}
        strategies = {}
        hours = {}
        for t in trades:
            for d, key in [(assets, t.asset), (strategies, t.strategy_id)]:
                if key not in d: d[key] = {"pnl": 0.0, "wins": 0}
                d[key]["pnl"] += (t.profit_usd or 0.0)
                if t.result == "win": d[key]["wins"] += 1
            
            # Hour logic
            hour = datetime.fromisoformat(t.open_time).hour
            if hour not in hours: hours[hour] = {"pnl": 0.0}
            hours[hour]["pnl"] += (t.profit_usd or 0.0)

        best_asset = max(assets.keys(), key=lambda x: assets[x]["pnl"]) if assets else ""
        best_strategy = max(strategies.keys(), key=lambda x: strategies[x]["pnl"]) if strategies else ""
        best_hour = max(hours.keys(), key=lambda x: hours[x]["pnl"]) if hours else 0

        return PerformanceReport(
            period_start=datetime.fromisoformat(trades[0].open_time),
            period_end=datetime.fromisoformat(trades[-1].open_time),
            total_trades=len(trades),
            wins=len(wins),
            losses=len(losses),
            draws=len(draws),
            winrate=round(winrate, 4),
            profit_factor=round(profit_factor, 2),
            total_pnl_usd=round(total_pnl, 2),
            max_drawdown_usd=round(max_dd_usd, 2),
            max_drawdown_pct=round(max_dd_pct, 4),
            sharpe_ratio=round(PerformanceAnalyzer.sharpe_ratio(trades), 2),
            avg_win_usd=round(gross_profit / len(wins), 2) if wins else 0.0,
            avg_loss_usd=round(gross_loss / len(losses), 2) if losses else 0.0,
            largest_win_usd=max([t.profit_usd for t in wins]) if wins else 0.0,
            largest_loss_usd=min([t.profit_usd for t in losses]) if losses else 0.0,
            max_consecutive_wins=max_c_wins,
            max_consecutive_losses=max_c_losses,
            avg_confidence=round(sum(t.signal_confidence for t in trades) / len(trades), 4),
            best_asset=best_asset,
            best_strategy=best_strategy,
            best_hour=best_hour
        )

    @staticmethod
    def max_drawdown(trades: List[TradeRecord]) -> Tuple[float, float]:
        if not trades: return 0.0, 0.0
        equity = 0.0
        peak = 0.0
        max_dd_usd = 0.0
        max_dd_pct = 0.0
        
        initial_capital = 1000.0 # Arbitrary for pct calculation if not provided
        current_balance = initial_capital
        
        for t in trades:
            pnl = t.profit_usd or 0.0
            current_balance += pnl
            if current_balance > peak:
                peak = current_balance
            
            dd_usd = peak - current_balance
            if dd_usd > max_dd_usd:
                max_dd_usd = dd_usd
                if peak > 0:
                    max_dd_pct = dd_usd / peak
                    
        return max_dd_usd, max_dd_pct

    @staticmethod
    def sharpe_ratio(trades: List[TradeRecord], risk_free: float = 0.0) -> float:
        returns = []
        for t in trades:
            if t.amount > 0 and t.profit_usd is not None:
                returns.append(t.profit_usd / t.amount)
        
        if len(returns) < 2: return 0.0
        
        ret_array = np.array(returns)
        mean_ret = np.mean(ret_array)
        std_ret = np.std(ret_array)
        
        if std_ret == 0: return 0.0
        return float((mean_ret - risk_free) / std_ret)
