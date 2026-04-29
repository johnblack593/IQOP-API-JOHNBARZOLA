import unittest
import numpy as np
from iqoptionapi.asset_scanner import AssetScanner, AssetScore

class TestAssetScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = AssetScanner(min_payout=0.80, optimal_vol=0.40)
        # Mock candles: 50 candles [open, high, low, close, volume]
        self.mock_candles = np.zeros((50, 5))
        self.mock_candles[:, 3] = np.linspace(1.1000, 1.1050, 50) # Close prices
        self.mock_candles[:, 1] = self.mock_candles[:, 3] + 0.0005 # Highs
        self.mock_candles[:, 2] = self.mock_candles[:, 3] - 0.0005 # Lows

    def test_score_zero_for_closed_asset(self):
        score = self.scanner.score_asset("EURUSD", self.mock_candles, 0.85, is_open=False)
        self.assertEqual(score.score, 0.0)

    def test_score_increases_with_payout(self):
        score1 = self.scanner.score_asset("EURUSD", self.mock_candles, 0.80)
        score2 = self.scanner.score_asset("EURUSD", self.mock_candles, 0.90)
        self.assertGreater(score2.score, score1.score)

    def test_get_best_assets_returns_top_n(self):
        candles_map = {"EURUSD": self.mock_candles, "GBPUSD": self.mock_candles}
        payouts_map = {"EURUSD": 0.82, "GBPUSD": 0.88}
        best = self.scanner.get_best_assets(["EURUSD", "GBPUSD"], candles_map, payouts_map, top_n=1)
        self.assertEqual(len(best), 1)
        self.assertEqual(best[0].asset, "GBPUSD")

    def test_is_worth_trading(self):
        score_obj = AssetScore("EURUSD", 0.90, True, 0.001, 0.75, "test")
        self.assertTrue(self.scanner.is_worth_trading(score_obj, min_score=0.6))
        self.assertFalse(self.scanner.is_worth_trading(score_obj, min_score=0.8))

    def test_score_between_zero_and_one(self):
        score = self.scanner.score_asset("EURUSD", self.mock_candles, 0.85)
        self.assertTrue(0.0 <= score.score <= 1.0)

if __name__ == '__main__':
    unittest.main()
