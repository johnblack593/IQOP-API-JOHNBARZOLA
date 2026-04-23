import unittest
from datetime import datetime, timezone
from iqoptionapi.performance import PerformanceAnalyzer, PerformanceReport
from iqoptionapi.trade_journal import TradeRecord

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc).isoformat()
        self.trades = [
            TradeRecord("1", "EURUSD", "call", 10.0, 60, "binary", "S1", 0.8, self.now, self.now, 1.1, 1.2, "win", 8.5),
            TradeRecord("2", "EURUSD", "put", 10.0, 60, "binary", "S1", 0.7, self.now, self.now, 1.2, 1.1, "win", 8.5),
            TradeRecord("3", "GBPUSD", "call", 10.0, 60, "binary", "S1", 0.9, self.now, self.now, 1.3, 1.2, "loss", -10.0),
        ]

    def test_winrate_correct(self):
        report = PerformanceAnalyzer.analyze(self.trades)
        self.assertEqual(report.winrate, 0.6667)

    def test_profit_factor(self):
        report = PerformanceAnalyzer.analyze(self.trades)
        # Gross profit = 17.0, Gross loss = 10.0
        self.assertEqual(report.profit_factor, 1.7)

    def test_max_drawdown(self):
        # Sequence: +8.5, +8.5, -10.0
        # Equity peak: 1017.0, Ends at: 1007.0
        # Max DD: 10.0
        report = PerformanceAnalyzer.analyze(self.trades)
        self.assertEqual(report.max_drawdown_usd, 10.0)

    def test_analyze_empty_returns_zeros(self):
        report = PerformanceAnalyzer.analyze([])
        self.assertEqual(report.total_trades, 0)
        self.assertEqual(report.winrate, 0.0)

    def test_max_consecutive_losses(self):
        trades = self.trades + [
            TradeRecord("4", "EURUSD", "call", 10.0, 60, "binary", "S1", 0.8, self.now, self.now, 1.1, 1.0, "loss", -10.0),
            TradeRecord("5", "EURUSD", "call", 10.0, 60, "binary", "S1", 0.8, self.now, self.now, 1.1, 1.0, "loss", -10.0),
        ]
        report = PerformanceAnalyzer.analyze(trades)
        self.assertEqual(report.max_consecutive_losses, 3)

if __name__ == '__main__':
    unittest.main()
