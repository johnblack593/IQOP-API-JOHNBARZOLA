import unittest
import os
import shutil
import json
from iqoptionapi.trade_journal import TradeJournal, TradeRecord
from iqoptionapi.strategy.signal import Signal, Direction, AssetType

class TestTradeJournal(unittest.TestCase):
    def setUp(self):
        self.test_dir = "tests/data/journal"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        self.journal = TradeJournal(journal_dir=self.test_dir)
        
        self.mock_signal = Signal(
            asset="EURUSD",
            direction=Direction.CALL,
            duration=60,
            amount=1.0,
            asset_type=AssetType.BINARY,
            confidence=0.85,
            strategy_id="TestStrategy"
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_open_trade_creates_record(self):
        record = self.journal.open_trade(self.mock_signal)
        self.assertEqual(record.asset, "EURUSD")
        self.assertEqual(record.direction, "call")
        self.assertIsNone(record.result)
        
        # Verify file exists and has 1 line
        filename = self.journal._get_filename()
        self.assertTrue(os.path.exists(filename))
        with open(filename, "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)

    def test_close_trade_updates_result(self):
        record = self.journal.open_trade(self.mock_signal)
        tid = record.trade_id
        
        updated = self.journal.close_trade(tid, "win", 0.85, 1.12345)
        self.assertEqual(updated.result, "win")
        self.assertEqual(updated.profit_usd, 0.85)
        self.assertEqual(updated.close_price, 1.12345)
        self.assertIsNotNone(updated.close_time)

    def test_jsonl_persistence_roundtrip(self):
        self.journal.open_trade(self.mock_signal)
        new_journal = TradeJournal(journal_dir=self.test_dir)
        trades = new_journal.get_trades_today()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].asset, "EURUSD")

    def test_session_summary(self):
        r1 = self.journal.open_trade(self.mock_signal)
        self.journal.close_trade(r1.trade_id, "win", 0.85)
        
        r2 = self.journal.open_trade(self.mock_signal)
        self.journal.close_trade(r2.trade_id, "loss", -1.0)
        
        summary = self.journal.get_session_summary()
        self.assertEqual(summary["total_trades"], 2)
        self.assertEqual(summary["wins"], 1)
        self.assertEqual(summary["losses"], 1)
        self.assertEqual(summary["winrate"], 0.5)
        self.assertAlmostEqual(summary["total_profit_usd"], -0.15)

    def test_close_nonexistent_trade_raises(self):
        with self.assertRaises(KeyError):
            self.journal.close_trade("invalid_id", "win", 1.0)

    def test_export_csv_creates_file(self):
        self.journal.open_trade(self.mock_signal)
        csv_path = os.path.join(self.test_dir, "test.csv")
        self.journal.export_csv(csv_path)
        self.assertTrue(os.path.exists(csv_path))

if __name__ == '__main__':
    unittest.main()
