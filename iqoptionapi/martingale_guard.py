"""
iqoptionapi/martingale_guard.py
───────────────────────────────
Control seguro de estrategias de gestión de capital.
"""
from enum import Enum
from typing import Optional


class MoneyManagement(str, Enum):
    FLAT            = "flat"
    MARTINGALE      = "martingale"
    ANTI_MARTINGALE = "anti_martingale"
    FIBONACCI       = "fibonacci"
    KELLY           = "kelly"

class MartingaleGuard:
    """
    Calcula el monto de la próxima operación con límites estrictos.
    """

    def __init__(
        self,
        strategy: MoneyManagement = MoneyManagement.FLAT,
        base_amount: float = 1.0,
        multiplier: float = 2.0,
        max_steps: int = 4,
        max_amount_usd: float = 50.0,
        max_balance_pct: float = 0.05,
    ) -> None:
        self.strategy = strategy
        self.base_amount = base_amount
        self.multiplier = multiplier
        self.max_steps = max_steps
        self.max_amount_usd = max_amount_usd
        self.max_balance_pct = max_balance_pct

        self._current_step = 0
        self._fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        self._last_amount = base_amount

    def next_amount(
        self,
        last_result: Optional[str],
        current_balance: float,
    ) -> float:
        """
        Calcula el monto de la próxima operación aplicando límites.
        """
        if last_result is None:
            amount = self.base_amount
            self._current_step = 0
        elif last_result == "draw":
            amount = self._last_amount # Re-trade same amount
        else:
            amount = self._calculate_raw_amount(last_result)

        # Apply Hard Caps
        capped_amount = min(amount, self.max_amount_usd)
        balance_cap = current_balance * self.max_balance_pct
        final_amount = min(capped_amount, balance_cap)
        
        # Ensure minimum trade amount (usually 1.0 in IQ)
        final_amount = max(1.0, final_amount)
        
        self._last_amount = final_amount
        return final_amount

    def _calculate_raw_amount(self, last_result: str) -> float:
        if self.strategy == MoneyManagement.FLAT:
            return self.base_amount

        if self.strategy == MoneyManagement.MARTINGALE:
            if last_result == "loss":
                self._current_step += 1
                if self._current_step > self.max_steps:
                    self._current_step = 0
                    return self.base_amount
                return self.base_amount * (self.multiplier ** self._current_step)
            else: # win
                self._current_step = 0
                return self.base_amount

        if self.strategy == MoneyManagement.ANTI_MARTINGALE:
            if last_result == "win":
                self._current_step += 1
                if self._current_step > self.max_steps:
                    self._current_step = 0
                    return self.base_amount
                return self.base_amount * (self.multiplier ** self._current_step)
            else: # loss
                self._current_step = 0
                return self.base_amount

        if self.strategy == MoneyManagement.FIBONACCI:
            if last_result == "loss":
                self._current_step = min(len(self._fib_sequence) - 1, self._current_step + 1)
                # Cap by max_steps too
                if self._current_step > self.max_steps:
                    self._current_step = 0
            else: # win
                self._current_step = max(0, self._current_step - 2)
            
            return self.base_amount * self._fib_sequence[self._current_step]

        return self.base_amount

    def reset(self) -> None:
        self._current_step = 0
        self._last_amount = self.base_amount

    def current_step(self) -> int:
        return self._current_step

    def risk_report(self) -> dict:
        return {
            "strategy": self.strategy,
            "current_step": self._current_step,
            "current_amount": self._last_amount,
            "total_at_risk_session": "calculated_elsewhere"
        }
