import unittest
from iqoptionapi.martingale_guard import MartingaleGuard, MoneyManagement

class TestMartingaleGuard(unittest.TestCase):
    def setUp(self):
        self.guard = MartingaleGuard(
            strategy=MoneyManagement.MARTINGALE,
            base_amount=2.0,
            multiplier=2.0,
            max_steps=3,
            max_amount_usd=50.0,
            max_balance_pct=0.10
        )

    def test_flat_always_returns_base(self):
        flat = MartingaleGuard(strategy=MoneyManagement.FLAT, base_amount=5.0)
        self.assertEqual(flat.next_amount("loss", 1000), 5.0)
        self.assertEqual(flat.next_amount("win", 1000), 5.0)

    def test_martingale_doubles_on_loss(self):
        self.assertEqual(self.guard.next_amount(None, 1000), 2.0)
        self.assertEqual(self.guard.next_amount("loss", 1000), 4.0)
        self.assertEqual(self.guard.next_amount("loss", 1000), 8.0)
        self.assertEqual(self.guard.next_amount("win", 1000), 2.0)

    def test_martingale_caps_at_max_steps(self):
        self.guard.next_amount("loss", 1000) # Step 1: 4.0
        self.guard.next_amount("loss", 1000) # Step 2: 8.0
        self.guard.next_amount("loss", 1000) # Step 3: 16.0
        # Should reset after step 3 loss
        self.assertEqual(self.guard.next_amount("loss", 1000), 2.0)

    def test_martingale_never_exceeds_max_usd(self):
        self.guard.max_amount_usd = 10.0
        self.guard.next_amount("loss", 1000) # 4.0
        self.guard.next_amount("loss", 1000) # 8.0
        # 16.0 exceeds 10.0
        self.assertEqual(self.guard.next_amount("loss", 1000), 10.0)

    def test_fibonacci_sequence_steps(self):
        fib = MartingaleGuard(strategy=MoneyManagement.FIBONACCI, base_amount=1.0)
        self.assertEqual(fib.next_amount("loss", 1000), 1.0) # Step 1: index 1 val 1
        self.assertEqual(fib.next_amount("loss", 1000), 2.0) # Step 2: index 2 val 2
        self.assertEqual(fib.next_amount("loss", 1000), 3.0) # Step 3: index 3 val 3
        self.assertEqual(fib.next_amount("win", 1000), 1.0)  # Step 3-2 = 1: index 1 val 1

    def test_reset_returns_to_base(self):
        self.guard.next_amount("loss", 1000)
        self.guard.reset()
        self.assertEqual(self.guard.current_step(), 0)

if __name__ == '__main__':
    unittest.main()
