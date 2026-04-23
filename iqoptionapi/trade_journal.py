"""
iqoptionapi/trade_journal.py
────────────────────────────
Registro estructurado de TODAS las operaciones en JSONL.
"""
import os
import json
import uuid
import threading
import csv
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict
from iqoptionapi.strategy.signal import Signal


@dataclass
class TradeRecord:
    """Una operación completa, del open al close."""
    trade_id:       str
    asset:          str
    direction:      str        # "call" / "put"
    amount:         float
    duration_secs:  int
    asset_type:     str
    strategy_id:    str
    signal_confidence: float
    open_time:      str        # ISO format UTC
    close_time:     Optional[str] = None
    open_price:     Optional[float] = None
    close_price:    Optional[float] = None
    result:         Optional[str] = None   # "win" / "loss" / "draw"
    profit_usd:     Optional[float] = None
    metadata:       dict = field(default_factory=dict)
    session_id:     str = ""

class TradeJournal:
    """
    Registra operaciones en JSONL y permite consultas básicas.
    """

    def __init__(
        self,
        journal_dir: str = "data/journal",
        session_id: Optional[str] = None,
    ) -> None:
        self.journal_dir = journal_dir
        self.session_id = session_id or str(uuid.uuid4())
        self._lock = threading.Lock()
        
        if not os.path.exists(self.journal_dir):
            os.makedirs(self.journal_dir, exist_ok=True)

    def _get_filename(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return os.path.join(self.journal_dir, f"trades_{date_str}.jsonl")

    def open_trade(self, signal: Signal, trade_id: Optional[str] = None) -> TradeRecord:
        record = TradeRecord(
            trade_id=trade_id or str(uuid.uuid4()),
            asset=signal.asset,
            direction=signal.direction.value,
            amount=signal.amount,
            duration_secs=signal.duration,
            asset_type=signal.asset_type.value,
            strategy_id=signal.strategy_id,
            signal_confidence=signal.confidence,
            open_time=datetime.now(timezone.utc).isoformat(),
            metadata=signal.metadata,
            session_id=self.session_id
        )
        
        self._persist(record)
        return record

    def close_trade(
        self,
        trade_id: str,
        result: str,
        profit_usd: float,
        close_price: Optional[float] = None,
    ) -> TradeRecord:
        with self._lock:
            filename = self._get_filename()
            records = []
            target_record = None
            
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line)
                        if data["trade_id"] == trade_id:
                            data["result"] = result
                            data["profit_usd"] = profit_usd
                            data["close_price"] = close_price
                            data["close_time"] = datetime.now(timezone.utc).isoformat()
                            target_record = TradeRecord(**data)
                            records.append(json.dumps(data))
                        else:
                            records.append(line.strip())
            
            if target_record:
                with open(filename, "w", encoding="utf-8") as f:
                    for r in records:
                        f.write(r + "\n")
                return target_record
            else:
                raise KeyError(f"Trade ID {trade_id} not found in journal.")

    def _persist(self, record: TradeRecord) -> None:
        with self._lock:
            filename = self._get_filename()
            with open(filename, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(record)) + "\n")

    def get_trades_today(self) -> List[TradeRecord]:
        filename = self._get_filename()
        trades = []
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        trades.append(TradeRecord(**json.loads(line)))
                    except Exception:
                        continue
        return trades

    def get_session_summary(self) -> dict:
        all_trades = self.get_trades_today()
        session_trades = [t for t in all_trades if t.session_id == self.session_id]
        
        if not session_trades:
            return {
                "total_trades": 0, "wins": 0, "losses": 0, "draws": 0,
                "winrate": 0.0, "total_profit_usd": 0.0
            }
            
        wins = len([t for t in session_trades if t.result == "win"])
        losses = len([t for t in session_trades if t.result == "loss"])
        draws = len([t for t in session_trades if t.result == "draw"])
        profits = [t.profit_usd for t in session_trades if t.profit_usd is not None]
        
        return {
            "total_trades": len(session_trades),
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "winrate": wins / (wins + losses) if (wins + losses) > 0 else 0.0,
            "total_profit_usd": sum(profits),
            "largest_win": max(profits) if profits else 0.0,
            "largest_loss": min(profits) if profits else 0.0,
            "avg_confidence": sum(t.signal_confidence for t in session_trades) / len(session_trades)
        }

    def export_csv(self, output_path: str) -> None:
        trades = self.get_trades_today()
        if not trades:
            return
            
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(trades[0]).keys())
            writer.writeheader()
            for t in trades:
                writer.writerow(asdict(t))
